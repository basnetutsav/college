import pandas as pd
import numpy as np
from pathlib import Path
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
from itertools import count

# -----------------------------
# Plotly + Streamlit Defaults
# -----------------------------
pio.templates.default = "plotly_white"
px.defaults.template = "plotly_white"

_plot_counter = count()
_widget_counter = count()


def pkey(prefix="plot"):
    return f"{prefix}_{next(_plot_counter)}"


def wkey(prefix="w"):
    return f"{prefix}_{next(_widget_counter)}"


# -----------------------------
# Page Config & Styling
# -----------------------------
st.set_page_config(
    page_title="Global Ammolite Dashboard – All Themes",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    :root{
      --bg: #FFFFFF;
      --text: #000000;
      --border: #D9D9D9;
      --soft: #F5F5F5;
    }

    /* App background + default text */
    html, body, [class*="css"], .stApp {
      font-size: 0.95rem !important;
      background: var(--bg) !important;
      color: var(--text) !important;
      font-family: SpaceGrotesk, system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif !important;
    }

    /* FORCE readable text everywhere (fixes faint/washed-out text) */
    .stApp, .stApp p, .stApp span, .stApp label, .stApp div, .stApp a, .stApp li, .stApp small {
      color: var(--text) !important;
      opacity: 1 !important;
    }

    .block-container {
      padding-top: 0.8rem;
      padding-bottom: 2.0rem;
      max-width: 1550px;
      background: var(--bg) !important;
      color: var(--text) !important;
    }

    div[data-testid="column"] { padding-left: 0.40rem; padding-right: 0.40rem; }

    /* Sidebar: force white background + black text */
    section[data-testid="stSidebar"] {
      background: var(--bg) !important;
      color: var(--text) !important;
      border-right: 1px solid var(--border) !important;
    }
    section[data-testid="stSidebar"] * {
      color: var(--text) !important;
      opacity: 1 !important;
    }

    /* Metric cards (keep your sizing) */
    [data-testid="metric-container"] {
      padding: 0.70rem 0.85rem !important;
      border-radius: 14px !important;
      background: var(--bg) !important;
      border: 1px solid var(--border) !important;
    }
    /* Metric label/value/delta -> BLACK + full opacity (fixes invisible KPIs) */
    [data-testid="metric-container"] [data-testid="stMetricLabel"],
    [data-testid="metric-container"] [data-testid="stMetricLabel"] * ,
    [data-testid="metric-container"] [data-testid="stMetricValue"],
    [data-testid="metric-container"] [data-testid="stMetricValue"] * ,
    [data-testid="metric-container"] [data-testid="stMetricDelta"],
    [data-testid="metric-container"] [data-testid="stMetricDelta"] * {
      color: #000000 !important;
      opacity: 1 !important;
    }
    [data-testid="metric-container"] [data-testid="stMetricValue"] {
      font-size: 1.55rem !important;
      overflow: visible !important;
      text-overflow: clip !important;
      white-space: normal !important;
      line-height: 1.2 !important;
    }

    /* Captions (Filtered view...) */
    [data-testid="stCaptionContainer"],
    [data-testid="stCaptionContainer"] * {
      color: #000000 !important;
      opacity: 1 !important;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab"] {
      font-size: 0.95rem;
      color: var(--text) !important;
      opacity: 1 !important;
    }

    /* Headings */
    h1,h2,h3,h4,h5,h6,
    .stMarkdown h1,.stMarkdown h2,.stMarkdown h3,.stMarkdown h4 {
      color: var(--text) !important;
      font-family: SpaceGroteskHeader, SpaceGrotesk, system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif !important;
      opacity: 1 !important;
    }

    /* -----------------------------
       ✅ INPUTS: WHITE BACKGROUND + BLACK TEXT (everywhere)
    ------------------------------ */

    /* Input shells */
    div[data-baseweb="select"] > div,
    div[data-baseweb="input"] input,
    div[data-baseweb="textarea"] textarea {
      background: #FFFFFF !important;
      color: #000000 !important;
      border: 1px solid var(--border) !important;
      border-radius: 10px !important;
      opacity: 1 !important;
    }

    /* Select internal input + text */
    div[data-baseweb="select"] input,
    div[data-baseweb="select"] span,
    div[data-baseweb="select"] div {
      color: #000000 !important;
      opacity: 1 !important;
    }

    /* Dropdown popovers (opened menu) */
    div[data-baseweb="popover"] *,
    ul[role="listbox"],
    li[role="option"] {
      background: #FFFFFF !important;
      color: #000000 !important;
      opacity: 1 !important;
    }
    li[role="option"]:hover { background: var(--soft) !important; }

    /* Multiselect tags */
    .stMultiSelect span[data-baseweb="tag"] {
      background: var(--soft) !important;
      color: #000000 !important;
      border: 1px solid var(--border) !important;
      opacity: 1 !important;
    }
    .stMultiSelect span[data-baseweb="tag"] svg { fill: #000000 !important; }

    /* Date / Number inputs */
    div[data-testid="stDateInput"] input,
    div[data-testid="stNumberInput"] input {
      background: #FFFFFF !important;
      color: #000000 !important;
      border: 1px solid var(--border) !important;
      border-radius: 10px !important;
      opacity: 1 !important;
    }

    /* Radio / Checkbox / Toggle / Slider text */
    .stRadio *, .stCheckbox *, .stToggle *, .stSlider * {
      color: #000000 !important;
      opacity: 1 !important;
    }

    /* Buttons (including file uploader button) */
    .stButton > button,
    button[data-testid^="stBaseButton"],
    button[kind] {
      background: #FFFFFF !important;
      color: #000000 !important;
      border: 1px solid #000000 !important;
      border-radius: 10px !important;
      opacity: 1 !important;
    }
    .stButton > button:hover,
    button[data-testid^="stBaseButton"]:hover,
    button[kind]:hover { background: var(--soft) !important; }
    .stButton > button * ,
    button[data-testid^="stBaseButton"] * ,
    button[kind] * { color: #000000 !important; opacity: 1 !important; }

    /* File uploader dropzone */
    div[data-testid="stFileUploaderDropzone"] {
      background: #FFFFFF !important;
      border: 1px dashed var(--border) !important;
    }
    div[data-testid="stFileUploaderDropzone"] * {
      color: #000000 !important;
      opacity: 1 !important;
    }

    /* Dataframes background */
    .stDataFrame, .stTable { background: #FFFFFF !important; }

    /* ✅ Highlight/Selection: keep text BLACK */
    ::selection { background: #E6E6E6 !important; color: #000000 !important; }
    ::-moz-selection { background: #E6E6E6 !important; color: #000000 !important; }
    input::selection, textarea::selection { background: #E6E6E6 !important; color: #000000 !important; }

    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------
# Helper: Deduplicate columns
# -----------------------------
def deduplicate_columns(df: pd.DataFrame) -> pd.DataFrame:
    new_cols = []
    seen = {}
    for col in df.columns:
        if col in seen:
            seen[col] += 1
            new_cols.append(f"{col}_{seen[col]}")
        else:
            seen[col] = 0
            new_cols.append(col)
    df.columns = new_cols
    return df


def safe_col(df: pd.DataFrame, col: str) -> bool:
    return col in df.columns


def to_num(df: pd.DataFrame, col: str):
    if safe_col(df, col):
        df[col] = pd.to_numeric(df[col], errors="coerce")


def style_fig(fig, height=430):
    # ✅ White chart background + black text + FIXED hoverlabel (no ValueError)
    fig.update_layout(
        height=height,
        margin=dict(l=10, r=10, t=55, b=40),
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
        font=dict(family="SpaceGrotesk", size=12, color="#000000"),
        legend=dict(
            font=dict(size=11, family="SpaceGrotesk", color="#000000"),
            orientation="h",
            yanchor="bottom", y=1.02,
            xanchor="left", x=0,
        ),
        hoverlabel=dict(
            font=dict(size=11, family="SpaceGrotesk", color="#000000"),
            bgcolor="#FFFFFF",
        ),
        xaxis=dict(
            title_font=dict(size=13, family="SpaceGrotesk", color="#000000"),
            tickfont=dict(size=11, family="SpaceGrotesk", color="#000000"),
            automargin=True,
        ),
        yaxis=dict(
            title_font=dict(size=13, family="SpaceGrotesk", color="#000000"),
            tickfont=dict(size=11, family="SpaceGrotesk", color="#000000"),
            automargin=True,
        ),
    )

    # maps
    try:
        fig.update_geos(bgcolor="#FFFFFF")
    except Exception:
        pass

    # Safe hovertemplate reset (some trace types don't support it)
    def _safe_unset_hovertemplate(tr):
        try:
            if "hovertemplate" in tr.to_plotly_json():
                tr.update(hovertemplate=None)
        except Exception:
            pass

    fig.for_each_trace(_safe_unset_hovertemplate)
    return fig


# -----------------------------
# Data Loading & Preparation
# -----------------------------
@st.cache_data(show_spinner=False)
def load_data(uploaded_file=None):
    # 1) Choose source
    csv_path = None
    if uploaded_file is None:
        possible_paths = [
            "Combined_Sales_2025.csv",
            "Combined_Sales_2025 (2).csv",
            "data/Combined_Sales_2025.csv",
            "/mnt/data/Combined_Sales_2025.csv",
        ]
        for p in possible_paths:
            if Path(p).exists():
                csv_path = p
                break

    # 2) Read CSV (robust encoding)
    def _read_csv(src):
        try:
            return pd.read_csv(src)
        except UnicodeDecodeError:
            try:
                return pd.read_csv(src, encoding="utf-8", encoding_errors="replace")
            except TypeError:
                return pd.read_csv(src, encoding="latin-1")

    if uploaded_file is not None:
        df = _read_csv(uploaded_file)
    else:
        if csv_path is None:
            st.error(
                "❌ CSV file not found.\n\n"
                "Option A: Upload your CSV in the sidebar.\n"
                "Option B: Put **Combined_Sales_2025.csv** in the same folder as this app."
            )
            st.stop()
        df = _read_csv(csv_path)

    # 3) Ensure unique column names
    df = deduplicate_columns(df)

    # 4) Trim object columns
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].astype(str).str.strip()

    # 5) Parse dates (safe)
    if safe_col(df, "Date"):
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    else:
        st.error("❌ Missing required column: 'Date'")
        st.stop()

    if safe_col(df, "Shipped Date"):
        df["Shipped Date"] = pd.to_datetime(df["Shipped Date"], errors="coerce")
    else:
        df["Shipped Date"] = pd.NaT

    # 6) Numeric conversions (safe)
    for c in ["Price (CAD)", "Discount (CAD)", "Shipping (CAD)", "Taxes Collected (CAD)",
              "length", "width", "weight", "Color Count (#)"]:
        to_num(df, c)

    # Fill core monetary columns if missing
    for c in ["Price (CAD)", "Discount (CAD)", "Shipping (CAD)", "Taxes Collected (CAD)"]:
        if not safe_col(df, c):
            df[c] = 0.0
        df[c] = df[c].fillna(0.0)

    # 7) Derived metrics
    df["Net Sales"] = df["Price (CAD)"] - df["Discount (CAD)"]
    df["Total Collected"] = df["Net Sales"] + df["Shipping (CAD)"] + df["Taxes Collected (CAD)"]
    df["OrderCount"] = 1

    # 8) Ownership
    if safe_col(df, "Consignment? (Y/N)"):
        df["Is Consigned"] = df["Consignment? (Y/N)"].astype(str).str.upper().eq("Y")
    else:
        df["Is Consigned"] = False
    df["Ownership"] = np.where(df["Is Consigned"], "Consigned", "Owned")

    # 9) Timing
    df["Days to Ship"] = (df["Shipped Date"] - df["Date"]).dt.days

    # 10) Area + price density
    if safe_col(df, "length") and safe_col(df, "width"):
        df["Area (mm²)"] = df["length"] * df["width"]
        df["Price per mm²"] = df["Net Sales"] / df["Area (mm²)"]
        df.loc[~np.isfinite(df["Price per mm²"]), "Price per mm²"] = np.nan
    else:
        df["Area (mm²)"] = np.nan
        df["Price per mm²"] = np.nan

    # 11) Time dimensions
    df["Year"] = df["Date"].dt.year
    df["Month"] = df["Date"].dt.to_period("M").dt.to_timestamp()
    df["Month Name"] = df["Date"].dt.strftime("%b")
    df["Month Number"] = df["Date"].dt.month
    df["Quarter"] = df["Date"].dt.to_period("Q").astype(str)
    df["Day Name"] = df["Date"].dt.day_name()
    df["Week"] = df["Date"].dt.to_period("W").apply(lambda r: r.start_time)

    # 12) Compliance
    if safe_col(df, "Export Permit (PDF link)"):
        df["Has Export Permit"] = (
            df["Export Permit (PDF link)"].astype(str).str.strip().ne("")
            & df["Export Permit (PDF link)"].notna()
        )
    else:
        df["Has Export Permit"] = False

    if safe_col(df, "COA #"):
        df["Has COA"] = df["COA #"].astype(str).str.strip().ne("") & df["COA #"].notna()
    else:
        df["Has COA"] = False

    if safe_col(df, "Country"):
        df["Country"] = df["Country"].fillna("Unknown").astype(str)
    else:
        df["Country"] = "Unknown"

    if safe_col(df, "City"):
        df["City"] = df["City"].fillna("Unknown").astype(str)
    else:
        df["City"] = "Unknown"

    if safe_col(df, "Channel"):
        df["Channel"] = df["Channel"].fillna("Unknown").astype(str)
    else:
        df["Channel"] = "Unknown"

    if safe_col(df, "Customer Type"):
        df["Customer Type"] = df["Customer Type"].fillna("Unknown").astype(str)
    else:
        df["Customer Type"] = "Unknown"

    if safe_col(df, "Customer Name"):
        df["Customer Name"] = df["Customer Name"].fillna("Unknown").astype(str)
    else:
        df["Customer Name"] = "Unknown"

    df["Is Export"] = df["Country"].ne("Canada")

    return df


# -----------------------------
# Sidebar: Data source + Filters
# -----------------------------
st.sidebar.title("Controls")

uploaded = st.sidebar.file_uploader(
    "Upload sales CSV (optional)",
    type=["csv"],
    key="upload_csv",
    help="If you upload here, it overrides searching for Combined_Sales_2025.csv in the folder.",
)

df = load_data(uploaded_file=uploaded)

min_date = df["Date"].min()
max_date = df["Date"].max()
if pd.isna(min_date) or pd.isna(max_date):
    st.error("❌ 'Date' column has no valid dates.")
    st.stop()

date_range = st.sidebar.date_input(
    "Sale Date range",
    value=(min_date.date(), max_date.date()),
    min_value=min_date.date(),
    max_value=max_date.date(),
    key="date_range",
)

# Core filters
country_options = sorted(df["Country"].dropna().unique())
channel_options = sorted(df["Channel"].dropna().unique())
cust_type_options = sorted(df["Customer Type"].dropna().unique())

sel_countries = st.sidebar.multiselect("Countries", options=country_options, default=[], key="countries")
sel_channels = st.sidebar.multiselect("Channels", options=channel_options, default=[], key="channels")
sel_cust = st.sidebar.multiselect("Customer types", options=cust_type_options, default=[], key="cust_types")

# Advanced filters
with st.sidebar.expander("More filters (optional)", expanded=False):
    prod_opts = sorted(df["Product Type"].dropna().unique()) if safe_col(df, "Product Type") else []
    grade_opts = sorted(df["Grade"].dropna().unique()) if safe_col(df, "Grade") else []
    finish_opts = sorted(df["Finish"].dropna().unique()) if safe_col(df, "Finish") else []

    sel_prod = st.multiselect("Product Type", options=prod_opts, default=[], key="prod_type")
    sel_grade = st.multiselect("Grade", options=grade_opts, default=[], key="grade")
    sel_finish = st.multiselect("Finish", options=finish_opts, default=[], key="finish")

    only_export = st.checkbox("Export only (Country != Canada)", value=False, key="only_export")
    only_consigned = st.checkbox("Consigned only", value=False, key="only_consigned")

    name_search = st.text_input("Customer name contains", value="", key="cust_search")

    max_rows = st.slider("Max rows to show in tables", 100, 3000, 500, step=100, key="max_rows")

metric_map = {
    "Net Sales (CAD)": "Net Sales",
    "Total Collected (CAD)": "Total Collected",
    "Order Count": "OrderCount",
}
metric_label = st.sidebar.selectbox("Main metric for charts", options=list(metric_map.keys()), index=0, key="metric")
metric_col = metric_map[metric_label]

compare_prev = st.sidebar.toggle("Show deltas vs previous period", value=True, key="compare_prev")


def apply_filters(data: pd.DataFrame, start, end) -> pd.DataFrame:
    mask = pd.Series(True, index=data.index)
    mask &= data["Date"].between(pd.to_datetime(start), pd.to_datetime(end))

    if sel_countries:
        mask &= data["Country"].isin(sel_countries)
    if sel_channels:
        mask &= data["Channel"].isin(sel_channels)
    if sel_cust:
        mask &= data["Customer Type"].isin(sel_cust)

    if safe_col(data, "Product Type") and sel_prod:
        mask &= data["Product Type"].isin(sel_prod)
    if safe_col(data, "Grade") and sel_grade:
        mask &= data["Grade"].isin(sel_grade)
    if safe_col(data, "Finish") and sel_finish:
        mask &= data["Finish"].isin(sel_finish)

    if only_export:
        mask &= data["Is Export"]
    if only_consigned:
        mask &= data["Is Consigned"]

    if name_search.strip():
        mask &= data["Customer Name"].str.contains(name_search.strip(), case=False, na=False)

    return data[mask].copy()


# Resolve date range
if isinstance(date_range, tuple) and len(date_range) == 2:
    cur_start, cur_end = date_range
else:
    cur_start, cur_end = min_date.date(), max_date.date()

f = apply_filters(df, cur_start, cur_end)

if f.empty:
    st.warning("No rows match the current filters. Try widening your filters on the left.")
    st.stop()

# Previous-period compare (same duration immediately before)
cur_days = (pd.to_datetime(cur_end) - pd.to_datetime(cur_start)).days + 1
prev_end = (pd.to_datetime(cur_start) - pd.Timedelta(days=1)).date()
prev_start = (pd.to_datetime(cur_start) - pd.Timedelta(days=cur_days)).date()
prev = apply_filters(df, prev_start, prev_end) if compare_prev else pd.DataFrame()


def fmt_money(x):
    return f"${x:,.0f}"


def fmt_int(x):
    return f"{int(x):,}"


# -----------------------------
# Title & KPI Row (with deltas)
# -----------------------------
st.title("💎 Global Ammolite Sales Dashboard – Advanced")

cur_total_metric = f[metric_col].sum()
cur_total_net = f["Net Sales"].sum()
cur_orders = len(f)
cur_unique = f["Customer Name"].nunique()
cur_cons_share = float(f["Is Consigned"].mean()) if cur_orders else 0.0
cur_avg_ship = float(f["Days to Ship"].dropna().mean()) if f["Days to Ship"].notna().any() else np.nan

# prev KPI
if compare_prev and not prev.empty:
    prev_total_metric = prev[metric_col].sum()
    prev_total_net = prev["Net Sales"].sum()
    prev_orders = len(prev)
    prev_unique = prev["Customer Name"].nunique()
    prev_cons_share = float(prev["Is Consigned"].mean()) if prev_orders else 0.0
    prev_avg_ship = float(prev["Days to Ship"].dropna().mean()) if prev["Days to Ship"].notna().any() else np.nan
else:
    prev_total_metric = prev_total_net = prev_orders = prev_unique = np.nan
    prev_cons_share = prev_avg_ship = np.nan

k1, k2, k3, k4, k5, k6 = st.columns(6)

with k1:
    if metric_col == "OrderCount":
        st.metric(
            metric_label,
            fmt_int(cur_total_metric),
            delta=(None if not np.isfinite(prev_total_metric) else f"{int(cur_total_metric - prev_total_metric):,}"),
        )
    else:
        st.metric(
            metric_label,
            fmt_money(cur_total_metric),
            delta=(None if not np.isfinite(prev_total_metric) else fmt_money(cur_total_metric - prev_total_metric)),
        )

with k2:
    st.metric(
        "Total Net Sales",
        fmt_money(cur_total_net),
        delta=(None if not np.isfinite(prev_total_net) else fmt_money(cur_total_net - prev_total_net)),
    )

with k3:
    st.metric(
        "Total Orders",
        fmt_int(cur_orders),
        delta=(None if not np.isfinite(prev_orders) else f"{int(cur_orders - prev_orders):,}"),
    )

with k4:
    st.metric(
        "Unique Customers",
        fmt_int(cur_unique),
        delta=(None if not np.isfinite(prev_unique) else f"{int(cur_unique - prev_unique):,}"),
    )

with k5:
    st.metric(
        "Consigned Share",
        f"{cur_cons_share*100:,.1f}%",
        delta=(None if not np.isfinite(prev_cons_share) else f"{(cur_cons_share - prev_cons_share)*100:,.1f}%"),
    )

with k6:
    if np.isfinite(cur_avg_ship):
        st.metric(
            "Avg Days to Ship",
            f"{cur_avg_ship:,.1f}",
            delta=(None if not np.isfinite(prev_avg_ship) else f"{(cur_avg_ship - prev_avg_ship):,.1f}"),
        )
    else:
        st.metric("Avg Days to Ship", "—")

st.caption(
    f"Filtered view: **{cur_start} → {cur_end}**"
    + (f" (compared to **{prev_start} → {prev_end}**)" if compare_prev else "")
)
st.markdown("---")

# -----------------------------
# MAIN TOPIC TABS
# -----------------------------
(
    tab_overview,
    tab_price,
    tab_mix,
    tab_segments,
    tab_geo,
    tab_timing,
    tab_ownership,
    tab_seasonality,
    tab_compliance,
    tab_data,
) = st.tabs(
    [
        "Overview",
        "Price Drivers",
        "Product Mix",
        "Customer Segments",
        "Geography & Channels",
        "Inventory Timing",
        "Ownership",
        "Seasonality",
        "Compliance",
        "All Data",
    ]
)

# -----------------------------
# TAB: Overview (more advanced)
# -----------------------------
with tab_overview:
    st.subheader("Executive Overview")

    c1, c2 = st.columns([1.6, 1])

    # Trend line with granularity
    with c1:
        gran = st.radio("Trend granularity", ["Daily", "Weekly", "Monthly"], horizontal=True, key="ov_gran")
        if gran == "Daily":
            ts = f.groupby("Date", as_index=False)[metric_col].sum().sort_values("Date")
            xcol = "Date"
        elif gran == "Weekly":
            ts = f.groupby("Week", as_index=False)[metric_col].sum().sort_values("Week")
            xcol = "Week"
        else:
            ts = f.groupby("Month", as_index=False)[metric_col].sum().sort_values("Month")
            xcol = "Month"

        if not ts.empty:
            ts["Rolling"] = ts[metric_col].rolling(3, min_periods=1).mean()
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=ts[xcol], y=ts[metric_col], mode="lines+markers", name=metric_label))
            fig.add_trace(go.Scatter(x=ts[xcol], y=ts["Rolling"], mode="lines", name="3-period avg"))
            fig.update_layout(title=f"{metric_label} Trend", xaxis_title="", yaxis_title=metric_label)
            fig = style_fig(fig, height=420)
            st.plotly_chart(fig, use_container_width=True, key=pkey("ov_trend"))

    # Pareto: Top countries share
    with c2:
        by_country = f.groupby("Country", as_index=False)[metric_col].sum().sort_values(metric_col, ascending=False)
        if not by_country.empty:
            topn = st.slider("Pareto top N", 5, 25, 10, key="ov_pareto_n")
            pareto = by_country.head(topn).copy()
            total = by_country[metric_col].sum()
            pareto["Share"] = pareto[metric_col] / total if total else 0
            pareto["CumShare"] = pareto["Share"].cumsum()

            fig = go.Figure()
            fig.add_trace(go.Bar(x=pareto["Country"], y=pareto[metric_col], name=metric_label))
            fig.add_trace(
                go.Scatter(
                    x=pareto["Country"],
                    y=pareto["CumShare"],
                    name="Cumulative share",
                    yaxis="y2",
                    mode="lines+markers",
                )
            )
            fig.update_layout(
                title=f"Pareto – Top {topn} Countries",
                xaxis_title="",
                yaxis_title=metric_label,
                yaxis2=dict(title="Cumulative share", overlaying="y", side="right", tickformat=".0%"),
            )
            fig = style_fig(fig, height=420)
            st.plotly_chart(fig, use_container_width=True, key=pkey("ov_pareto"))

    st.markdown("#### Snapshot: Top Performers")
    c3, c4, c5 = st.columns(3)

    with c3:
        by_channel = f.groupby("Channel", as_index=False)[metric_col].sum().sort_values(metric_col, ascending=False)
        fig = px.bar(by_channel, x="Channel", y=metric_col, text_auto=".2s", title=f"{metric_label} by Channel")
        fig.update_layout(xaxis_title="", yaxis_title=metric_label)
        fig = style_fig(fig, height=380)
        st.plotly_chart(fig, use_container_width=True, key=pkey("ov_channel"))

    with c4:
        if safe_col(f, "Product Type"):
            by_prod = (
                f.groupby("Product Type", as_index=False)[metric_col]
                .sum()
                .sort_values(metric_col, ascending=False)
                .head(12)
            )
            fig = px.bar(
                by_prod,
                x=metric_col,
                y="Product Type",
                orientation="h",
                text_auto=".2s",
                title=f"Top Product Types by {metric_label}",
            )
            fig.update_layout(xaxis_title=metric_label, yaxis_title="")
            fig = style_fig(fig, height=380)
            st.plotly_chart(fig, use_container_width=True, key=pkey("ov_prod"))
        else:
            st.info("No 'Product Type' column found.")

    with c5:
        seg = f.groupby("Customer Type", as_index=False)[metric_col].sum().sort_values(metric_col, ascending=False)
        fig = px.pie(seg, names="Customer Type", values=metric_col, hole=0.35, title=f"{metric_label} Share by Customer Type")
        fig = style_fig(fig, height=380)
        st.plotly_chart(fig, use_container_width=True, key=pkey("ov_seg"))

    # Auto insights
    top_country = by_country["Country"].iloc[0] if not by_country.empty else "N/A"
    top_channel = by_channel["Channel"].iloc[0] if not by_channel.empty else "N/A"
    share_top = float(by_country[metric_col].iloc[0] / by_country[metric_col].sum()) if by_country[metric_col].sum() > 0 else np.nan

    st.markdown("### Key Takeaways")
    bullets = []
    if np.isfinite(share_top):
        bullets.append(f"- **{top_country}** is #1, contributing **{share_top*100:.1f}%** of {metric_label.lower()} in this view.")
    bullets.append(f"- **{top_channel}** is the leading channel for the selected filters.")
    if np.isfinite(cur_avg_ship):
        bullets.append(f"- Average time to ship is **{cur_avg_ship:.1f} days** (use *Inventory Timing* to see channel differences).")
    bullets.append("- Use *Price Drivers* to see which attributes push price up/down, and *Compliance* to spot risk gaps.")
    st.markdown("\n".join(bullets))
# -----------------------------
# TAB: Price Drivers / Visualization (5 tabs + 9 visuals)
# -----------------------------
with tab_price:
    st.subheader("Price Drivers / Visualization")

    p_df = f.copy()

    # Revenue (total sales value): prefer Net Sales, else Price
    if safe_col(p_df, "Net Sales"):
        revenue_col = "Net Sales"
    elif safe_col(p_df, "Price (CAD)"):
        revenue_col = "Price (CAD)"
    else:
        revenue_col = metric_col  # fallback

    # Unit price (average price): prefer Price (CAD), else revenue_col
    price_col = "Price (CAD)" if safe_col(p_df, "Price (CAD)") else revenue_col

    # Most recent year in filtered view (matches your screenshots like 2025)
    year_pick = int(p_df["Year"].dropna().max()) if safe_col(p_df, "Year") and p_df["Year"].notna().any() else None
    p_year = p_df[p_df["Year"] == year_pick].copy() if year_pick is not None else p_df.copy()

    # 5 Tabs
    t1, t2, t3, t4, t5 = st.tabs(
        [
            "Average Price by Product Type & Grade",
            "Sales Performance by Dominant Color",
            "Monthly Sales Value vs Average Price Trend",
            "Monthly Total Sales Value Trend (Revenue)",
            "Next Fiscal Year Seasonal Forecast (30% Growth)",
        ]
    )

    # -----------------------------
    # TAB 1 (1 visual)
    # Average Price by Product Type & Grade
    # -----------------------------
    with t1:
        if safe_col(p_df, "Product Type") and safe_col(p_df, "Grade") and safe_col(p_df, price_col):
            tmp = p_df.dropna(subset=["Product Type", "Grade", price_col]).copy()
            avg_ptg = (
                tmp.groupby(["Product Type", "Grade"], as_index=False)
                .agg(Avg_Price=(price_col, "mean"), Num_Sales=("OrderCount", "sum"))
            )

            fig = px.bar(
                avg_ptg,
                x="Product Type",
                y="Avg_Price",
                color="Grade",
                barmode="group",
                title="Average Price by Product Type & Grade",
                hover_data={"Num_Sales": True, "Avg_Price": ":,.0f"},
            )
            fig.update_layout(xaxis_title="Product Type", yaxis_title="Avg Price (CAD)")
            fig.update_yaxes(tickprefix="$", separatethousands=True)
            fig.update_xaxes(tickangle=-25)
            fig = style_fig(fig, height=520)
            st.plotly_chart(fig, use_container_width=True, key=pkey("pd_viz_tab1"))

            with st.expander("Insights - Average Price by Product Type & Grade", expanded=False):
                st.markdown(
                    """
**Insights:** Shows how discounting relates to net sale value and highlights if large discounts are driving larger baskets.

**Why it helps:** Helps manage promotions without unintentionally eroding margins.

**Recommendations:**  
- If discounts don’t meaningfully lift net sale value, reduce discount depth or tighten eligibility.  
- Create tiered offers (e.g., discounts only above certain cart values) to protect profitability.
"""
                )

            st.divider()
        else:
            st.info("Missing required columns for this chart (need Product Type, Grade, and a price column).")
    # -----------------------------
    # TAB 2 (2 visuals)
    # Sales Performance by Dominant Color
    # -----------------------------
    with t2:
        st.markdown("### Sales Performance by Dominant Color")

        if safe_col(p_df, "Dominant Color") and safe_col(p_df, revenue_col) and safe_col(p_df, price_col):
            tmp = p_df.dropna(subset=["Dominant Color"]).copy()

            dom = (
                tmp.groupby("Dominant Color", as_index=False)
                .agg(
                    Total_Revenue=(revenue_col, "sum"),
                    Avg_Price=(price_col, "mean"),
                )
            )

            dom_rev = dom.sort_values("Total_Revenue", ascending=False)
            dom_avg = dom.sort_values("Avg_Price", ascending=False)

            c1, c2 = st.columns(2)

            with c1:
                fig1 = px.bar(
                    dom_rev,
                    x="Dominant Color",
                    y="Total_Revenue",
                    title="Total Revenue by Dominant Color",
                )
                fig1.update_layout(xaxis_title="Dominant Color", yaxis_title="Total Sales Value (CAD)")
                fig1.update_yaxes(tickprefix="$", separatethousands=True)
                fig1.update_xaxes(tickangle=-60)
                fig1 = style_fig(fig1, height=470)
                st.plotly_chart(fig1, use_container_width=True, key=pkey("pd_viz_tab2_rev"))

            with c2:
                fig2 = px.bar(
                    dom_avg,
                    x="Dominant Color",
                    y="Avg_Price",
                    title="Average Price by Dominant Color",
                )
                fig2.update_layout(xaxis_title="Dominant Color", yaxis_title="Average Price (CAD)")
                fig2.update_yaxes(tickprefix="$", separatethousands=True)
                fig2.update_xaxes(tickangle=-60)
                fig2 = style_fig(fig2, height=470)
                st.plotly_chart(fig2, use_container_width=True, key=pkey("pd_viz_tab2_avg"))

         with st.expander("Insights - Average Price by Product Type & Grade", expanded=False):
                st.markdown(
                    """
**Insights:** Shows how discounting relates to net sale value and highlights if large discounts are driving larger baskets.

**Why it helps:** Helps manage promotions without unintentionally eroding margins.

**Recommendations:**  
- If discounts don’t meaningfully lift net sale value, reduce discount depth or tighten eligibility.  
- Create tiered offers (e.g., discounts only above certain cart values) to protect profitability.
"""
                )

            st.divider()
        else:
            st.info("Missing 'Dominant Color' or required price/revenue columns for this tab.")

    # -----------------------------
    # TAB 3 (2 visuals)
    # Monthly Sales Value Vs Average price trend
    # -----------------------------
    with t3:
        st.markdown("### Monthly Sales Value Vs Average price trend")

        if year_pick is None or not safe_col(p_year, "Month"):
            st.info("Missing Month/Year info to build monthly trends.")
        else:
            c1, c2 = st.columns(2)

            # (1) Monthly Average Price Trend by Grade
            with c1:
                st.markdown("#### Monthly Average Price (CAD) Trend (Price Power)")
                if safe_col(p_year, "Grade") and safe_col(p_year, price_col):
                    g = (
                        p_year.dropna(subset=["Month", "Grade", price_col])
                        .groupby(["Month", "Grade"], as_index=False)
                        .agg(Avg_Price=(price_col, "mean"))
                        .sort_values("Month")
                    )
                    fig = px.line(
                        g,
                        x="Month",
                        y="Avg_Price",
                        color="Grade",
                        markers=True,
                        title="Average Price Trend",
                    )
                    fig.update_layout(xaxis_title=f"Date ({year_pick})", yaxis_title="Average Price (CAD)")
                    fig.update_yaxes(tickprefix="$", separatethousands=True)
                    fig.update_xaxes(tickformat="%b")
                    fig = style_fig(fig, height=470)
                    st.plotly_chart(fig, use_container_width=True, key=pkey("pd_viz_tab3_grade"))
                else:
                    st.info("Need 'Grade' and a price column to plot this trend.")

            # (2) Monthly Average Price Trend by Color Count
            with c2:
                st.markdown("#### Monthly Average Price (CAD) Trend by Color Count (Price Power)")
                if safe_col(p_year, "Color Count (#)") and safe_col(p_year, price_col):
                    cc = p_year.dropna(subset=["Month", "Color Count (#)", price_col]).copy()
                    cc["Color Count (#)"] = cc["Color Count (#)"].round(0).astype("Int64").astype(str)

                    g2 = (
                        cc.groupby(["Month", "Color Count (#)"], as_index=False)
                        .agg(Avg_Price=(price_col, "mean"))
                        .sort_values("Month")
                    )
                    fig2 = px.line(
                        g2,
                        x="Month",
                        y="Avg_Price",
                        color="Color Count (#)",
                        markers=True,
                        title="Average Price Trend by Color Count",
                    )
                    fig2.update_layout(xaxis_title=f"Date ({year_pick})", yaxis_title="Average Price (CAD)")
                    fig2.update_yaxes(tickprefix="$", separatethousands=True)
                    fig2.update_xaxes(tickformat="%b")
                    fig2 = style_fig(fig2, height=470)
                    st.plotly_chart(fig2, use_container_width=True, key=pkey("pd_viz_tab3_cc"))

                 with st.expander("Insights - Average Price by Product Type & Grade", expanded=False):
                st.markdown(
                    """
**Insights:** Shows how discounting relates to net sale value and highlights if large discounts are driving larger baskets.

**Why it helps:** Helps manage promotions without unintentionally eroding margins.

**Recommendations:**  
- If discounts don’t meaningfully lift net sale value, reduce discount depth or tighten eligibility.  
- Create tiered offers (e.g., discounts only above certain cart values) to protect profitability.
"""
                )

            st.divider()

                else:
                    st.info("Need 'Color Count (#)' and a price column to plot this trend.")

    # -----------------------------
    # TAB 4 (3 visuals)
    # Monthly Total Sales Value Trend (Revenue)
    # -----------------------------
    with t4:
        st.markdown("### Monthly Total Sales Value Trend (Revenue)")

        if year_pick is None or not safe_col(p_year, "Month"):
            st.info("Missing Month/Year info to build monthly revenue trends.")
        else:
            top = st.columns(2)

            # (1) Monthly Total Sales Value Trend by Grade
            with top[0]:
                st.markdown("#### Monthly Total Sales Value (CAD) Trend by Grade (Revenue)")
                if safe_col(p_year, "Grade") and safe_col(p_year, revenue_col):
                    gr = (
                        p_year.dropna(subset=["Month", "Grade", revenue_col])
                        .groupby(["Month", "Grade"], as_index=False)
                        .agg(Total_Sales=(revenue_col, "sum"))
                        .sort_values("Month")
                    )
                    fig = px.line(
                        gr,
                        x="Month",
                        y="Total_Sales",
                        color="Grade",
                        markers=True,
                        title="Total Sales Value Trend (by Grade)",
                    )
                    fig.update_layout(xaxis_title=f"Date ({year_pick})", yaxis_title="Total Sales Value (CAD)")
                    fig.update_yaxes(tickprefix="$", separatethousands=True)
                    fig.update_xaxes(tickformat="%b")
                    fig = style_fig(fig, height=420)
                    st.plotly_chart(fig, use_container_width=True, key=pkey("pd_viz_tab4_grade"))
                else:
                    st.info("Need 'Grade' and a revenue column to plot this trend.")

            # (2) Monthly Total Sales Value Trend by Color Count
            with top[1]:
                st.markdown("#### Monthly Total Sales Value (CAD) Trend by Color Count (Revenue)")
                if safe_col(p_year, "Color Count (#)") and safe_col(p_year, revenue_col):
                    cc = p_year.dropna(subset=["Month", "Color Count (#)", revenue_col]).copy()
                    cc["Color Count (#)"] = cc["Color Count (#)"].round(0).astype("Int64").astype(str)

                    cr = (
                        cc.groupby(["Month", "Color Count (#)"], as_index=False)
                        .agg(Total_Sales=(revenue_col, "sum"))
                        .sort_values("Month")
                    )
                    fig2 = px.line(
                        cr,
                        x="Month",
                        y="Total_Sales",
                        color="Color Count (#)",
                        markers=True,
                        title="Total Sales Value Trend (by Color Count)",
                    )
                    fig2.update_layout(xaxis_title=f"Date ({year_pick})", yaxis_title="Total Sales Value (CAD)")
                    fig2.update_yaxes(tickprefix="$", separatethousands=True)
                    fig2.update_xaxes(tickformat="%b")
                    fig2 = style_fig(fig2, height=420)
                    st.plotly_chart(fig2, use_container_width=True, key=pkey("pd_viz_tab4_cc"))
                else:
                    st.info("Need 'Color Count (#)' and a revenue column to plot this trend.")

            # (3) Monthly Total Sales Value Trend (Overall)
            st.markdown("#### Monthly Total Sales Value (CAD) Trend (Overall)")
            if safe_col(p_year, revenue_col):
                overall = (
                    p_year.dropna(subset=["Month", revenue_col])
                    .groupby("Month", as_index=False)
                    .agg(Total_Sales=(revenue_col, "sum"))
                    .sort_values("Month")
                )
                fig3 = px.line(
                    overall,
                    x="Month",
                    y="Total_Sales",
                    markers=True,
                    title="Overall Total Sales Value Trend",
                )
                fig3.update_layout(xaxis_title=f"Date ({year_pick})", yaxis_title="Total Sales Value (CAD)")
                fig3.update_yaxes(tickprefix="$", separatethousands=True)
                fig3.update_xaxes(tickformat="%b")
                fig3 = style_fig(fig3, height=520)
                st.plotly_chart(fig3, use_container_width=True, key=pkey("pd_viz_tab4_overall"))

             with st.expander("Insights - Average Price by Product Type & Grade", expanded=False):
                st.markdown(
                    """
**Insights:** Shows how discounting relates to net sale value and highlights if large discounts are driving larger baskets.

**Why it helps:** Helps manage promotions without unintentionally eroding margins.

**Recommendations:**  
- If discounts don’t meaningfully lift net sale value, reduce discount depth or tighten eligibility.  
- Create tiered offers (e.g., discounts only above certain cart values) to protect profitability.
"""
                )

            st.divider()
            
            else:
                st.info("Need a revenue column to plot the overall trend.")

    # -----------------------------
    # TAB 5 (1 visual, but 2-panel layout like your screenshot)
    # Next Fiscal Year Seasonal Forecast Model (30% Growth)
    # -----------------------------
    with t5:
        st.markdown("### Next Fiscal Year Seasonal Forecast Model (30% Growth)")
        st.caption("Based on the Google: 30% is the significant increase yearly driven by Rarity and Diminishing Supply.")

        if safe_col(p_df, "Product Type") and safe_col(p_df, "Grade") and safe_col(p_df, price_col) and safe_col(p_df, "Month") and safe_col(p_df, "Year"):
            left, right = st.columns(2)

            prod_opts = sorted([x for x in p_df["Product Type"].dropna().unique().tolist() if str(x).strip() != ""])
            grade_opts = sorted([x for x in p_df["Grade"].dropna().unique().tolist() if str(x).strip() != ""])

            sel_prod = st.selectbox("Select Product Type:", options=prod_opts, key="pd_fc_prod")
            sel_grade = st.selectbox("Select Grade:", options=grade_opts, key="pd_fc_grade")

            sub = p_df[(p_df["Product Type"] == sel_prod) & (p_df["Grade"] == sel_grade)].copy()
            if sub.empty:
                st.info("No rows match that Product Type + Grade under current filters.")
            else:
                base_year = int(sub["Year"].dropna().max())
                forecast_year = base_year + 1

                # Actual series (base year)
                actual = (
                    sub[sub["Year"] == base_year]
                    .dropna(subset=["Month", price_col])
                    .groupby("Month", as_index=False)
                    .agg(Avg_Price=(price_col, "mean"))
                    .sort_values("Month")
                )

                # Ensure 12-month frame for consistent seasonality mapping
                months_base = pd.date_range(f"{base_year}-01-01", periods=12, freq="MS")
                actual_full = pd.DataFrame({"Month": months_base}).merge(actual, on="Month", how="left")

                # Forecast: repeat seasonality (lower bound) + 30% growth (upper bound)
                months_fc = pd.date_range(f"{forecast_year}-01-01", periods=12, freq="MS")
                fc = pd.DataFrame({"Month": months_fc})
                fc["Lower Bound"] = actual_full["Avg_Price"].values
                fc["Upper Bound"] = actual_full["Avg_Price"].values * 1.30

                with left:
                    fig_a = px.line(
                        actual_full,
                        x="Month",
                        y="Avg_Price",
                        markers=True,
                        title=f"Actual Monthly Average Price ({base_year})<br>{sel_prod} ({sel_grade})",
                    )
                    fig_a.update_layout(xaxis_title="Date", yaxis_title="Average Price (CAD)")
                    fig_a.update_yaxes(tickprefix="$", separatethousands=True)
                    fig_a.update_xaxes(tickformat="%b %Y")
                    fig_a = style_fig(fig_a, height=520)
                    st.plotly_chart(fig_a, use_container_width=True, key=pkey("pd_fc_actual"))

                with right:
                    fig_f = go.Figure()
                    fig_f.add_trace(go.Scatter(
                        x=fc["Month"], y=fc["Lower Bound"],
                        mode="lines+markers",
                        name=f"{forecast_year} Forecast: Lower Bound"
                    ))
                    fig_f.add_trace(go.Scatter(
                        x=fc["Month"], y=fc["Upper Bound"],
                        mode="lines+markers",
                        name=f"{forecast_year} Forecast: Upper Bound"
                    ))
                    fig_f.update_layout(
                        title=f"Forecast Monthly Average Price ({forecast_year})",
                        xaxis_title="Date",
                        yaxis_title="Average Price (CAD)",
                    )
                    fig_f.update_yaxes(tickprefix="$", separatethousands=True)
                    fig_f.update_xaxes(tickformat="%b %Y")
                    fig_f = style_fig(fig_f, height=520)
                    st.plotly_chart(fig_f, use_container_width=True, key=pkey("pd_fc_forecast"))

         with st.expander("Insights - Average Price by Product Type & Grade", expanded=False):
                st.markdown(
                    """
**Insights:** Shows how discounting relates to net sale value and highlights if large discounts are driving larger baskets.

**Why it helps:** Helps manage promotions without unintentionally eroding margins.

**Recommendations:**  
- If discounts don’t meaningfully lift net sale value, reduce discount depth or tighten eligibility.  
- Create tiered offers (e.g., discounts only above certain cart values) to protect profitability.
"""
                )

            st.divider()
        
        else:
            st.info("Missing required columns for forecasting (need Product Type, Grade, Month, Year, and a price column).")


# -----------------------------
# TAB: Product Mix (more advanced)
# -----------------------------
with tab_mix:
    st.subheader("Product Mix – Revenue, Volume, and Structure")
    m_df = f.copy()

    m_tabs = st.tabs(["Overview", "Channel Mix (100%)", "Structure (Sunburst)", "Sankey", "Data"])

    with m_tabs[0]:
        if safe_col(m_df, "Product Type"):
            by_prod = m_df.groupby("Product Type", as_index=False)[metric_col].sum().sort_values(metric_col, ascending=False)
            fig1 = px.bar(by_prod.head(18), x="Product Type", y=metric_col, title=f"Top Product Types by {metric_label}", text_auto=".2s")
            fig1.update_layout(xaxis_title="", yaxis_title=metric_label)
            fig1 = style_fig(fig1, height=430)
            st.plotly_chart(fig1, use_container_width=True, key=pkey("mix_prod"))

            avg_by_prod = m_df.groupby("Product Type", as_index=False)["Net Sales"].mean().sort_values("Net Sales", ascending=False).head(18)
            fig2 = px.bar(avg_by_prod, x="Net Sales", y="Product Type", orientation="h", title="Average Net Sales per Order – by Product Type", text_auto=".0f")
            fig2.update_layout(xaxis_title="Avg Net Sales (CAD)", yaxis_title="")
            fig2 = style_fig(fig2, height=470)
            st.plotly_chart(fig2, use_container_width=True, key=pkey("mix_avg"))
        else:
            st.info("No 'Product Type' column found.")

    with m_tabs[1]:
        if safe_col(m_df, "Product Type"):
            mix = m_df.groupby(["Product Type", "Channel"], as_index=False)[metric_col].sum()
            totals = mix.groupby("Product Type", as_index=False)[metric_col].sum().rename(columns={metric_col: "Total"})
            mix = mix.merge(totals, on="Product Type", how="left")
            mix["Share"] = np.where(mix["Total"] > 0, mix[metric_col] / mix["Total"], 0)

            top_prod = totals.sort_values("Total", ascending=False).head(12)["Product Type"].tolist()
            mix2 = mix[mix["Product Type"].isin(top_prod)].copy()

            fig = px.bar(
                mix2,
                x="Product Type",
                y="Share",
                color="Channel",
                barmode="stack",
                title="Channel Mix by Product Type (100% stacked, Top 12)",
            )
            fig.update_layout(xaxis_title="", yaxis_title="Share", yaxis_tickformat=".0%")
            fig = style_fig(fig, height=460)
            st.plotly_chart(fig, use_container_width=True, key=pkey("mix_100"))
        else:
            st.info("No 'Product Type' column found.")

    with m_tabs[2]:
        path = [c for c in ["Product Type", "Grade", "Finish"] if safe_col(m_df, c)]
        if len(path) >= 2:
            fig = px.sunburst(m_df, path=path, values=metric_col, title=f"{metric_label} Structure (Sunburst)")
            fig = style_fig(fig, height=520)
            st.plotly_chart(fig, use_container_width=True, key=pkey("mix_sun"))
        else:
            st.info("Need at least 2 columns among Product Type / Grade / Finish for sunburst.")

    with m_tabs[3]:
        st.markdown("#### Sankey (Channel → Product Type → Grade)")
        if safe_col(m_df, "Product Type") and safe_col(m_df, "Grade"):
            sank = m_df.groupby(["Channel", "Product Type", "Grade"], as_index=False)[metric_col].sum()
            sank = sank[sank[metric_col] > 0].copy()

            top_prod = m_df.groupby("Product Type")[metric_col].sum().sort_values(ascending=False).head(12).index
            sank = sank[sank["Product Type"].isin(top_prod)]

            labels = pd.Index(pd.concat([sank["Channel"], sank["Product Type"], sank["Grade"]]).unique()).tolist()
            idx = {lab: i for i, lab in enumerate(labels)}

            a = sank.groupby(["Channel", "Product Type"], as_index=False)[metric_col].sum()
            b = sank.groupby(["Product Type", "Grade"], as_index=False)[metric_col].sum()

            src = [idx[x] for x in a["Channel"]] + [idx[x] for x in b["Product Type"]]
            tgt = [idx[x] for x in a["Product Type"]] + [idx[x] for x in b["Grade"]]
            val = a[metric_col].tolist() + b[metric_col].tolist()

            fig = go.Figure(data=[go.Sankey(
                node=dict(label=labels, pad=14, thickness=14),
                link=dict(source=src, target=tgt, value=val),
            )])
            fig.update_layout(title=f"Sankey – {metric_label}", height=520, margin=dict(l=10, r=10, t=60, b=10))
            fig = style_fig(fig, height=520)
            st.plotly_chart(fig, use_container_width=True, key=pkey("mix_sankey"))
        else:
            st.info("Need 'Product Type' and 'Grade' columns for this Sankey view.")

    with m_tabs[4]:
        cols = ["Sale ID", "Date", "Product Type", "Grade", "Finish", "Channel", "Country", metric_col, "Net Sales"]
        cols = [c for c in cols if c in m_df.columns]
        subset = m_df[cols].copy()
        subset = subset.loc[:, ~subset.columns.duplicated()]
        st.dataframe(subset.head(max_rows), use_container_width=True)
        st.download_button(
            "Download product-mix subset (CSV)",
            data=subset.to_csv(index=False).encode("utf-8"),
            file_name="product_mix_subset.csv",
            mime="text/csv",
            key="dl_mix",
        )

# -----------------------------
# TAB: Customer Segments (RFM added)
# -----------------------------
with tab_segments:
    st.subheader("Customer Segments – Who Buys and Who Matters?")
    s_df = f.copy()

    s_tabs = st.tabs(["Overview", "Segment × Channel", "Customer Value", "RFM", "Data"])

    with s_tabs[0]:
        seg = s_df.groupby("Customer Type", as_index=False)[metric_col].sum().sort_values(metric_col, ascending=False)
        fig1 = px.bar(seg, x="Customer Type", y=metric_col, title=f"{metric_label} by Customer Segment", text_auto=".2s")
        fig1.update_layout(xaxis_title="", yaxis_title=metric_label)
        fig1 = style_fig(fig1, height=430)
        st.plotly_chart(fig1, use_container_width=True, key=pkey("seg_bar"))

        fig2 = px.pie(seg, names="Customer Type", values=metric_col, title=f"Share of {metric_label} by Segment", hole=0.35)
        fig2 = style_fig(fig2, height=430)
        st.plotly_chart(fig2, use_container_width=True, key=pkey("seg_pie"))

    with s_tabs[1]:
        seg_ch = s_df.groupby(["Customer Type", "Channel"], as_index=False)[metric_col].sum()
        fig = px.bar(seg_ch, x="Customer Type", y=metric_col, color="Channel", barmode="stack", title=f"{metric_label} by Segment × Channel")
        fig.update_layout(xaxis_title="", yaxis_title=metric_label)
        fig = style_fig(fig, height=470)
        st.plotly_chart(fig, use_container_width=True, key=pkey("seg_stack"))

    with s_tabs[2]:
        cust_stats = (
            s_df.groupby(["Customer Name", "Customer Type"], as_index=False)
            .agg(
                Orders=("Sale ID", "count") if safe_col(s_df, "Sale ID") else ("OrderCount", "sum"),
                Total_Net_Sales=("Net Sales", "sum"),
                Avg_Order=("Net Sales", "mean"),
            )
            .sort_values("Total_Net_Sales", ascending=False)
        )

        c1, c2 = st.columns([1.2, 1])
        with c1:
            st.markdown("#### Top 20 Customers by Net Sales")
            st.dataframe(cust_stats.head(20).style.format({"Total_Net_Sales": "{:,.0f}", "Avg_Order": "{:,.0f}"}), use_container_width=True)

        with c2:
            fig = px.scatter(
                cust_stats,
                x="Orders",
                y="Total_Net_Sales",
                color="Customer Type",
                size="Avg_Order",
                title="Customer Value – Orders vs Total Net Sales (bubble = avg order)",
                hover_data=["Customer Name"],
            )
            fig.update_layout(xaxis_title="Orders", yaxis_title="Total Net Sales (CAD)")
            fig = style_fig(fig, height=430)
            st.plotly_chart(fig, use_container_width=True, key=pkey("seg_scatter"))

    with s_tabs[3]:
        st.markdown("#### RFM (Recency, Frequency, Monetary)")
        ref_date = s_df["Date"].max()
        rfm = (
            s_df.groupby("Customer Name", as_index=False)
            .agg(
                LastPurchase=("Date", "max"),
                Frequency=("OrderCount", "sum"),
                Monetary=("Net Sales", "sum"),
            )
        )
        rfm["RecencyDays"] = (ref_date - rfm["LastPurchase"]).dt.days
        rfm = rfm.replace([np.inf, -np.inf], np.nan).dropna(subset=["RecencyDays", "Frequency", "Monetary"])

        c1, c2 = st.columns([1, 1])
        with c1:
            fig = px.scatter(
                rfm,
                x="RecencyDays",
                y="Monetary",
                size="Frequency",
                title="RFM Bubble: Recency vs Monetary (size = Frequency)",
                hover_data=["Customer Name"],
            )
            fig.update_layout(xaxis_title="Recency (days since last purchase)", yaxis_title="Total Net Sales (CAD)")
            fig = style_fig(fig, height=450)
            st.plotly_chart(fig, use_container_width=True, key=pkey("rfm_bubble"))

        with c2:
            rfm["R_Tier"] = pd.qcut(rfm["RecencyDays"], 4, labels=["Best", "Good", "Okay", "At Risk"])
            rfm["F_Tier"] = pd.qcut(rfm["Frequency"].rank(method="first"), 4, labels=["Low", "Mid", "High", "Top"])
            rfm["M_Tier"] = pd.qcut(rfm["Monetary"].rank(method="first"), 4, labels=["Low", "Mid", "High", "Top"])
            tier = (
                rfm.groupby(["R_Tier", "F_Tier"], as_index=False)["Monetary"].mean()
                .pivot(index="R_Tier", columns="F_Tier", values="Monetary")
                .fillna(0)
                .round(0)
            )

            fig = px.imshow(
                tier,
                aspect="auto",
                title="Average Monetary by Recency Tier × Frequency Tier",
                labels=dict(x="Frequency Tier", y="Recency Tier", color="Avg Monetary"),
            )
            fig = style_fig(fig, height=450)
            st.plotly_chart(fig, use_container_width=True, key=pkey("rfm_hm"))

    with s_tabs[4]:
        cols = ["Sale ID", "Date", "Customer Name", "Customer Type", "Country", "City", "Channel", metric_col, "Net Sales"]
        cols = [c for c in cols if c in s_df.columns]
        subset = s_df[cols].copy()
        subset = subset.loc[:, ~subset.columns.duplicated()]
        st.dataframe(subset.head(max_rows), use_container_width=True)
        st.download_button(
            "Download customer-segment subset (CSV)",
            data=subset.to_csv(index=False).encode("utf-8"),
            file_name="customer_segments_subset.csv",
            mime="text/csv",
            key="dl_segments",
        )

# -----------------------------
# TAB: Geography & Channels (upgraded)
# -----------------------------
with tab_geo:
    st.subheader("Geography & Channels")
    g_df = f.copy()

    g_tabs = st.tabs(["Overview", "World Map", "Channel Map", "Country × Channel", "Top Markets", "Data"])

    with g_tabs[0]:
        by_c = g_df.groupby("Country", as_index=False)[metric_col].sum().sort_values(metric_col, ascending=False)
        by_ch = g_df.groupby("Channel", as_index=False)[metric_col].sum().sort_values(metric_col, ascending=False)

        c1, c2, c3 = st.columns([1, 1, 1])
        with c1:
            fig = px.bar(by_c.head(12), x="Country", y=metric_col, title=f"Top Countries by {metric_label}", text_auto=".2s")
            fig.update_layout(xaxis_title="", yaxis_title=metric_label)
            fig = style_fig(fig, height=390)
            st.plotly_chart(fig, use_container_width=True, key=pkey("geo_topc"))

        with c2:
            fig = px.bar(by_ch, x="Channel", y=metric_col, title=f"{metric_label} by Channel", text_auto=".2s")
            fig.update_layout(xaxis_title="", yaxis_title=metric_label)
            fig = style_fig(fig, height=390)
            st.plotly_chart(fig, use_container_width=True, key=pkey("geo_topch"))

        with c3:
            top = by_c.head(10)["Country"]
            mix = g_df[g_df["Country"].isin(top)].groupby(["Country", "Channel"], as_index=False)[metric_col].sum()
            totals = mix.groupby("Country", as_index=False)[metric_col].sum().rename(columns={metric_col: "Total"})
            mix = mix.merge(totals, on="Country", how="left")
            mix["Share"] = np.where(mix["Total"] > 0, mix[metric_col] / mix["Total"], 0)

            fig = px.bar(mix, x="Country", y="Share", color="Channel", barmode="stack", title="Channel Share within Top Countries (100%)")
            fig.update_layout(xaxis_title="", yaxis_title="Share", yaxis_tickformat=".0%")
            fig = style_fig(fig, height=390)
            st.plotly_chart(fig, use_container_width=True, key=pkey("geo_share"))

    with g_tabs[1]:
        st.markdown("#### World Map (All Channels)")
        country_totals = g_df.groupby("Country", as_index=False)[metric_col].sum()
        if not country_totals.empty:
            fig = px.choropleth(
                country_totals,
                locations="Country",
                locationmode="country names",
                color=metric_col,
                hover_name="Country",
                title=f"{metric_label} by Country",
            )
            fig.update_layout(margin=dict(l=0, r=0, t=40, b=0))
            fig = style_fig(fig, height=520)
            st.plotly_chart(fig, use_container_width=True, key=pkey("geo_map_all"))
        else:
            st.info("No country data available for current filters.")

    with g_tabs[2]:
        st.markdown("#### Channel-Specific Map")
        ch_pick = st.selectbox("Pick channel", options=sorted(g_df["Channel"].unique()), key="geo_ch_pick")
        g2 = g_df[g_df["Channel"] == ch_pick].groupby("Country", as_index=False)[metric_col].sum()
        if not g2.empty:
            fig = px.choropleth(
                g2,
                locations="Country",
                locationmode="country names",
                color=metric_col,
                hover_name="Country",
                title=f"{metric_label} by Country – Channel: {ch_pick}",
            )
            fig = style_fig(fig, height=520)
            st.plotly_chart(fig, use_container_width=True, key=pkey("geo_map_ch"))
        else:
            st.info("No data for that channel in current filters.")

    with g_tabs[3]:
        st.markdown("#### Country × Channel Heatmap (Top Countries)")
        top_n = st.slider("Top N countries for heatmap", 3, 30, 12, key="geo_heat_top")
        country_totals = g_df.groupby("Country")[metric_col].sum().sort_values(ascending=False)
        top_idx = country_totals.head(top_n).index
        df_top = g_df[g_df["Country"].isin(top_idx)]
        pv = df_top.pivot_table(values=metric_col, index="Country", columns="Channel", aggfunc="sum", fill_value=0).round(0)

        if not pv.empty:
            hm = px.imshow(
                pv,
                labels=dict(x="Channel", y="Country", color=metric_label),
                title=f"{metric_label} Heatmap – Country × Channel",
                aspect="auto",
            )
            hm = style_fig(hm, height=520)
            st.plotly_chart(hm, use_container_width=True, key=pkey("geo_hm"))
        else:
            st.info("Heatmap is empty for current settings.")

    with g_tabs[4]:
        st.markdown("#### Top Markets & Cities")
        city_rev = g_df.groupby(["Country", "City"], as_index=False)[metric_col].sum().sort_values(metric_col, ascending=False).head(20)
        fig = px.bar(
            city_rev,
            x=metric_col,
            y="City",
            color="Country",
            orientation="h",
            title=f"Top City Markets by {metric_label}",
            text_auto=".2s",
        )
        fig.update_layout(xaxis_title=metric_label, yaxis_title="City")
        fig = style_fig(fig, height=520)
        st.plotly_chart(fig, use_container_width=True, key=pkey("geo_city"))

    with g_tabs[5]:
        cols = ["Sale ID", "Date", "Country", "City", "Channel", "Customer Type", metric_col, "Net Sales"]
        cols = [c for c in cols if c in g_df.columns]
        subset = g_df[cols].copy()
        subset = subset.loc[:, ~subset.columns.duplicated()]
        st.dataframe(subset.head(max_rows), use_container_width=True)
        st.download_button(
            "Download geography subset (CSV)",
            data=subset.to_csv(index=False).encode("utf-8"),
            file_name="geography_channels_subset.csv",
            mime="text/csv",
            key="dl_geo",
        )

# -----------------------------
# TAB: Inventory Timing (new visuals)
# -----------------------------
with tab_timing:
    st.subheader("Inventory Timing – Speed from Sale to Shipment")
    t_df = f.dropna(subset=["Days to Ship"]).copy()

    t_tabs = st.tabs(["SLA Snapshot", "Distributions", "By Channel (Advanced)", "Trend", "Data"])

    if t_df.empty:
        st.info("No valid Days to Ship data for the current filters.")
    else:
        with t_tabs[0]:
            sla = st.slider("SLA target (days)", 1, 60, 7, key="sla_days")
            within = (t_df["Days to Ship"] <= sla).mean()
            avg_lag = t_df["Days to Ship"].mean()
            p90 = t_df["Days to Ship"].quantile(0.90)
            p95 = t_df["Days to Ship"].quantile(0.95)

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("SLA Hit Rate", f"{within*100:,.1f}%")
            c2.metric("Avg Days to Ship", f"{avg_lag:,.1f}")
            c3.metric("P90 Days", f"{p90:,.1f}")
            c4.metric("P95 Days", f"{p95:,.1f}")

            gauge = go.Figure(go.Indicator(
                mode="gauge+number",
                value=within * 100,
                number={"suffix": "%"},
                title={"text": f"Percent shipped within {sla} days"},
                gauge={"axis": {"range": [0, 100]}}
            ))
            gauge.update_layout(height=320, margin=dict(l=10, r=10, t=60, b=10))
            gauge = style_fig(gauge, height=320)
            st.plotly_chart(gauge, use_container_width=True, key=pkey("tim_gauge"))

        with t_tabs[1]:
            fig = px.histogram(t_df, x="Days to Ship", nbins=40, title="Distribution of Days to Ship")
            fig.update_layout(xaxis_title="Days to Ship", yaxis_title="Orders")
            fig = style_fig(fig, height=430)
            st.plotly_chart(fig, use_container_width=True, key=pkey("tim_hist"))

            fig2 = px.box(t_df, x="Ownership", y="Days to Ship", points="all", title="Days to Ship by Ownership")
            fig2 = style_fig(fig2, height=430)
            st.plotly_chart(fig2, use_container_width=True, key=pkey("tim_own"))

        with t_tabs[2]:
            st.markdown("#### By Channel (two strong views)")
            c1, c2 = st.columns(2)

            with c1:
                fig = px.violin(
                    t_df,
                    x="Channel",
                    y="Days to Ship",
                    box=True,
                    points="all",
                    title="Days to Ship by Channel (Violin)",
                )
                fig.update_layout(xaxis_title="Channel", yaxis_title="Days to Ship")
                fig = style_fig(fig, height=470)
                st.plotly_chart(fig, use_container_width=True, key=pkey("tim_violin_ch"))

            with c2:
                bins = [-np.inf, 3, 7, 14, 30, np.inf]
                labels = ["0–3", "4–7", "8–14", "15–30", "31+"]
                t_df["Ship Bucket"] = pd.cut(t_df["Days to Ship"], bins=bins, labels=labels)

                dist = (
                    t_df.groupby(["Channel", "Ship Bucket"], as_index=False)
                    .size()
                    .rename(columns={"size": "Orders"})
                )
                totals = dist.groupby("Channel", as_index=False)["Orders"].sum().rename(columns={"Orders": "Total"})
                dist = dist.merge(totals, on="Channel", how="left")
                dist["Share"] = np.where(dist["Total"] > 0, dist["Orders"] / dist["Total"], 0)

                fig2 = px.bar(
                    dist,
                    x="Channel",
                    y="Share",
                    color="Ship Bucket",
                    barmode="stack",
                    title="Shipping Speed Mix by Channel (100% buckets)",
                )
                fig2.update_layout(yaxis_tickformat=".0%", xaxis_title="", yaxis_title="Share")
                fig2 = style_fig(fig2, height=470)
                st.plotly_chart(fig2, use_container_width=True, key=pkey("tim_bucket"))

        with t_tabs[3]:
            monthly_ship = t_df.groupby("Month", as_index=False)["Days to Ship"].mean().sort_values("Month")
            fig = px.line(monthly_ship, x="Month", y="Days to Ship", markers=True, title="Average Days to Ship – Monthly Trend")
            fig.update_layout(xaxis_title="Month", yaxis_title="Days to Ship")
            fig = style_fig(fig, height=430)
            st.plotly_chart(fig, use_container_width=True, key=pkey("tim_trend"))

        with t_tabs[4]:
            cols = ["Sale ID", "Date", "Country", "Channel", "Ownership", "Days to Ship", "Net Sales"]
            cols = [c for c in cols if c in t_df.columns]
            subset = t_df[cols].copy()
            subset = subset.loc[:, ~subset.columns.duplicated()]
            st.dataframe(subset.head(max_rows), use_container_width=True)
            st.download_button(
                "Download timing subset (CSV)",
                data=subset.to_csv(index=False).encode("utf-8"),
                file_name="inventory_timing_subset.csv",
                mime="text/csv",
                key="dl_timing",
            )

# -----------------------------
# TAB: Ownership (upgrade)
# -----------------------------
with tab_ownership:
    st.subheader("Ownership – Consigned vs Owned")
    o_df = f.copy()
    o_tabs = st.tabs(["Overview", "Value per Order", "Timing", "Data"])

    with o_tabs[0]:
        own_rev = o_df.groupby("Ownership", as_index=False)[metric_col].sum().sort_values(metric_col, ascending=False)
        fig = px.bar(own_rev, x="Ownership", y=metric_col, title=f"{metric_label} by Ownership", text_auto=".2s")
        fig.update_layout(xaxis_title="", yaxis_title=metric_label)
        fig = style_fig(fig, height=420)
        st.plotly_chart(fig, use_container_width=True, key=pkey("own_bar"))

        own_cnt = o_df.groupby("Ownership", as_index=False)["OrderCount"].sum().rename(columns={"OrderCount": "Orders"})
        fig2 = px.pie(own_cnt, names="Ownership", values="Orders", hole=0.35, title="Share of Orders – Consigned vs Owned")
        fig2 = style_fig(fig2, height=420)
        st.plotly_chart(fig2, use_container_width=True, key=pkey("own_pie"))

    with o_tabs[1]:
        stats = o_df.groupby("Ownership", as_index=False).agg(
            Orders=("OrderCount", "sum"),
            NetSales=("Net Sales", "sum"),
        )
        stats["NetSalesPerOrder"] = np.where(stats["Orders"] > 0, stats["NetSales"] / stats["Orders"], np.nan)
        fig = px.bar(stats, x="Ownership", y="NetSalesPerOrder", title="Net Sales per Order by Ownership", text_auto=".0f")
        fig.update_layout(yaxis_title="Net Sales / Order (CAD)", xaxis_title="")
        fig = style_fig(fig, height=420)
        st.plotly_chart(fig, use_container_width=True, key=pkey("own_value"))

    with o_tabs[2]:
        tdf = o_df.dropna(subset=["Days to Ship"]).copy()
        if tdf.empty:
            st.info("No valid Days to Ship data.")
        else:
            fig = px.violin(tdf, x="Ownership", y="Days to Ship", box=True, points="all", title="Days to Ship by Ownership (Violin)")
            fig = style_fig(fig, height=430)
            st.plotly_chart(fig, use_container_width=True, key=pkey("own_tim"))

    with o_tabs[3]:
        cols = ["Sale ID", "Date", "Country", "Channel", "Ownership", metric_col, "Net Sales"]
        cols = [c for c in cols if c in o_df.columns]
        subset = o_df[cols].copy()
        subset = subset.loc[:, ~subset.columns.duplicated()]
        st.dataframe(subset.head(max_rows), use_container_width=True)
        st.download_button(
            "Download ownership subset (CSV)",
            data=subset.to_csv(index=False).encode("utf-8"),
            file_name="ownership_subset.csv",
            mime="text/csv",
            key="dl_own",
        )

# -----------------------------
# TAB: Seasonality (upgrade)
# -----------------------------
with tab_seasonality:
    st.subheader("Seasonality – Time Patterns in Sales")
    se_df = f.copy()

    se_tabs = st.tabs(["Monthly Trend", "Month × Channel", "Year × Month Heatmap", "Day-of-week", "Data"])

    with se_tabs[0]:
        monthly = se_df.groupby("Month", as_index=False)[metric_col].sum().sort_values("Month")
        fig = px.line(monthly, x="Month", y=metric_col, markers=True, title=f"Monthly {metric_label}")
        fig.update_layout(xaxis_title="Month", yaxis_title=metric_label)
        fig = style_fig(fig, height=430)
        st.plotly_chart(fig, use_container_width=True, key=pkey("sea_month"))

        quarter = se_df.groupby("Quarter", as_index=False)[metric_col].sum().sort_values("Quarter")
        fig2 = px.bar(quarter, x="Quarter", y=metric_col, title=f"{metric_label} by Quarter", text_auto=".2s")
        fig2.update_layout(xaxis_title="Quarter", yaxis_title=metric_label)
        fig2 = style_fig(fig2, height=430)
        st.plotly_chart(fig2, use_container_width=True, key=pkey("sea_q"))

    with se_tabs[1]:
        month_channel = se_df.pivot_table(index="Month Name", columns="Channel", values=metric_col, aggfunc="sum").fillna(0)
        month_order = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
        month_channel = month_channel.reindex([m for m in month_order if m in month_channel.index])
        if not month_channel.empty:
            hm = px.imshow(
                month_channel,
                labels=dict(x="Channel", y="Month", color=metric_label),
                title=f"Seasonality Heatmap – Month × Channel ({metric_label})",
                aspect="auto",
            )
            hm = style_fig(hm, height=480)
            st.plotly_chart(hm, use_container_width=True, key=pkey("sea_hm_mc"))
        else:
            st.info("No data to display for Month × Channel.")

    with se_tabs[2]:
        ym = se_df.copy()
        ym["MonthShort"] = ym["Date"].dt.strftime("%b")
        pv = ym.pivot_table(index="Year", columns="MonthShort", values=metric_col, aggfunc="sum").fillna(0)
        pv = pv.reindex(columns=[m for m in ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"] if m in pv.columns])
        if not pv.empty and pv.shape[0] >= 1:
            hm = px.imshow(
                pv.round(0),
                aspect="auto",
                title=f"{metric_label} Heatmap – Year × Month",
                labels=dict(x="Month", y="Year", color=metric_label),
            )
            hm = style_fig(hm, height=450)
            st.plotly_chart(hm, use_container_width=True, key=pkey("sea_hm_ym"))
        else:
            st.info("Not enough data for Year × Month heatmap.")

    with se_tabs[3]:
        dow = se_df.groupby("Day Name", as_index=False)[metric_col].sum()
        dow_order = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
        dow["Day Name"] = pd.Categorical(dow["Day Name"], categories=dow_order, ordered=True)
        dow = dow.sort_values("Day Name")
        fig = px.bar(dow, x="Day Name", y=metric_col, title=f"{metric_label} by Day of Week", text_auto=".2s")
        fig.update_layout(xaxis_title="Day of Week", yaxis_title=metric_label)
        fig = style_fig(fig, height=430)
        st.plotly_chart(fig, use_container_width=True, key=pkey("sea_dow"))

    with se_tabs[4]:
        cols = ["Sale ID", "Date", "Country", "Channel", "Month", "Quarter", "Day Name", metric_col, "Net Sales"]
        cols = [c for c in cols if c in se_df.columns]
        subset = se_df[cols].copy()
        subset = subset.loc[:, ~subset.columns.duplicated()]
        st.dataframe(subset.head(max_rows), use_container_width=True)
        st.download_button(
            "Download seasonality subset (CSV)",
            data=subset.to_csv(index=False).encode("utf-8"),
            file_name="seasonality_subset.csv",
            mime="text/csv",
            key="dl_season",
        )
# -----------------------------
# TAB: Compliance (with DIR expanders + metric tiles for all 7 charts)
# -----------------------------
with tab_compliance:
    st.subheader("Compliance – COA & Export Permits")

    # Base = your dashboard's already-filtered dataframe
    c_base = f.copy()

    import math

    # -----------------------------
    # Prep (local to Compliance tab only)
    # -----------------------------
    if "Price (CAD)" in c_base.columns:
        c_base["Price (CAD)"] = pd.to_numeric(c_base["Price (CAD)"], errors="coerce")

    if "Date" in c_base.columns:
        c_base["Date"] = pd.to_datetime(c_base["Date"], errors="coerce")
    if "Shipped Date" in c_base.columns:
        c_base["Shipped Date"] = pd.to_datetime(c_base["Shipped Date"], errors="coerce")

    # COA Status
    if "COA #" in c_base.columns:
        coa_str = c_base["COA #"].astype(str).str.strip()
        c_base["COA_Clean"] = coa_str.replace({"": None, "nan": None, "NaN": None, "None": None})

        valid_mask = c_base["COA_Clean"].notna() & c_base["COA_Clean"].str.match(r"^COA-\d{6}$")
        invalid_mask = c_base["COA_Clean"].notna() & ~valid_mask

        c_base["COA Status"] = "No COA"
        c_base.loc[valid_mask, "COA Status"] = "With COA"
        c_base.loc[invalid_mask, "COA Status"] = "Invalid COA"
    elif "Has COA" in c_base.columns:
        c_base["COA Status"] = np.where(c_base["Has COA"].fillna(False), "With COA", "No COA")
    else:
        c_base["COA Status"] = "No COA"

    # Export permit clean column
    if "Export Permit (PDF link)" in c_base.columns:
        permit_str = c_base["Export Permit (PDF link)"].astype(str).str.strip()
        c_base["Export_Permit_Clean"] = permit_str.replace({"": None, "nan": None, "NaN": None, "None": None})
    else:
        c_base["Export_Permit_Clean"] = None

    # Days_to_Ship
    if "Days to Ship" in c_base.columns:
        c_base["Days_to_Ship"] = pd.to_numeric(c_base["Days to Ship"], errors="coerce")
    elif "Date" in c_base.columns and "Shipped Date" in c_base.columns:
        c_base["Days_to_Ship"] = (c_base["Shipped Date"] - c_base["Date"]).dt.days
    else:
        c_base["Days_to_Ship"] = np.nan

    # ProdGrade helper
    pt = c_base["Product Type"].fillna("Unknown Product").astype(str) if "Product Type" in c_base.columns else "Unknown Product"
    gr = c_base["Grade"].fillna("Unknown Grade").astype(str) if "Grade" in c_base.columns else "Unknown Grade"
    c_base["ProdGrade"] = pt + " | " + gr

    # Warn about invalid COA rows
    invalid_count = int((c_base["COA Status"] == "Invalid COA").sum()) if "COA Status" in c_base.columns else 0
    if invalid_count > 0:
        st.warning(f"{invalid_count} rows have **Invalid COA** format and are excluded when COA selector is **All**.")
        with st.expander("Show invalid COA rows (excluded)"):
            show_cols = [c for c in ["Sale ID", "COA #", "Product Type", "Grade", "Price (CAD)", "Country", "Customer Name"] if c in c_base.columns]
            st.dataframe(c_base.loc[c_base["COA Status"] == "Invalid COA", show_cols].head(200), use_container_width=True)

    def _apply_coa_selector(df_in: pd.DataFrame, widget_key: str) -> pd.DataFrame:
        choice = st.selectbox(
            "COA selector",
            ["All", "With COA", "Without COA"],
            index=0,
            key=widget_key,
        )
        df = df_in.copy()
        # "All" excludes invalid
        df = df[df["COA Status"] != "Invalid COA"]

        if choice == "With COA":
            return df[df["COA Status"] == "With COA"]
        if choice == "Without COA":
            return df[df["COA Status"] == "No COA"]
        return df

    def _fmt_money(x):
        if x is None or (isinstance(x, float) and not np.isfinite(x)):
            return "—"
        return f"${x:,.0f}"

    def _fmt_num(x):
        if x is None or (isinstance(x, float) and not np.isfinite(x)):
            return "—"
        if isinstance(x, (int, np.integer)):
            return f"{int(x):,}"
        return f"{x:,.1f}"

    def _fmt_pct(x):
        if x is None or (isinstance(x, float) and not np.isfinite(x)):
            return "—"
        return f"{x:.1f}%"

    # Expander with sub-tabs + metric tiles
    def render_dir_expander_metrics(title: str, definitions_md: str, metrics: list[dict], recommendations_md: str):
        with st.expander(f"📌 {title}: Definitions / Insights / Recommendations", expanded=False):
            dtab, itab, rtab = st.tabs(["Definitions", "Insights", "Recommendations"])

            with dtab:
                st.markdown(definitions_md)

            with itab:
                if not metrics:
                    st.info("No quick stats available for the current filters.")
                else:
                    cols = st.columns(3)
                    for i, m in enumerate(metrics):
                        with cols[i % 3]:
                            st.metric(
                                label=m.get("label", ""),
                                value=m.get("value", "—"),
                                delta=m.get("delta", None),
                                help=m.get("help", None),
                            )

            with rtab:
                st.markdown(recommendations_md)

    # -----------------------------
    # Sub-tabs (one per chart)
    # -----------------------------
    t1, t2, t3, t4, t5, t6, t7 = st.tabs(
        [
            "Chart 1 – Price vs Date",
            "Chart 2 – COA Premium by Grade",
            "Chart 3 – Shipping by Country & Grade",
            "Chart 4 – COA Adoption by Price Bucket",
            "Chart 5 – Shipping Delay vs Compliance",
            "Chart 6 – Compliance Score vs Order Value",
            "Chart 7 – COA Coverage by Product Type",
        ]
    )

    # ======================
    # Chart 1
    # ======================
    with t1:
        st.markdown("### Chart 1: Price vs Date (trendlines by Product Type + Grade)")
        c_df = _apply_coa_selector(c_base, "coa_sel_chart1")

        if c_df.empty or "Date" not in c_df.columns or "Price (CAD)" not in c_df.columns:
            st.info("No data available for Chart 1 under current filters.")
        else:
            fig = px.scatter(
                c_df.dropna(subset=["Date", "Price (CAD)"]),
                x="Date",
                y="Price (CAD)",
                color="ProdGrade",
                symbol="COA Status",
                trendline="ols",
                trendline_scope="trace",
                hover_data=[c for c in ["Sale ID", "Product Type", "Grade", "Country", "Customer Name"] if c in c_df.columns],
                title="Price vs Date by Product+Grade (symbol = COA Status)",
            )
            fig = style_fig(fig, height=520)
            st.plotly_chart(fig, use_container_width=True, key=pkey("comp_chart1"))
         

        # DIR expander
        total_rows = int(len(c_df))
        rows_with_price = int(c_df["Price (CAD)"].notna().sum()) if "Price (CAD)" in c_df.columns else 0
        unique_prodgrade = int(c_df["ProdGrade"].nunique()) if "ProdGrade" in c_df.columns else 0
        coa_rate = float((c_df["COA Status"] == "With COA").mean() * 100) if ("COA Status" in c_df.columns and len(c_df) > 0) else None
        date_min = c_df["Date"].min() if "Date" in c_df.columns else None
        date_max = c_df["Date"].max() if "Date" in c_df.columns else None
        avg_price = float(c_df["Price (CAD)"].mean()) if "Price (CAD)" in c_df.columns else None
        med_price = float(c_df["Price (CAD)"].median()) if "Price (CAD)" in c_df.columns else None

        top_prodgrade = None
        if "ProdGrade" in c_df.columns and len(c_df) > 0:
            vc = c_df["ProdGrade"].value_counts()
            top_prodgrade = vc.index[0] if len(vc) else None
            top_prodgrade_n = int(vc.iloc[0]) if len(vc) else None
        else:
            top_prodgrade_n = None

        definitions_md = """
**What this chart shows**
- **Each point** is a sale.
- **Color = Product Type | Grade** (`ProdGrade`).
- **Symbol = COA Status**.
- **Trendline (OLS)** estimates the direction of price over time for each trace.
"""
        metrics = [
            {"label": "Rows in view", "value": _fmt_num(total_rows), "help": "After global filters + COA selector"},
            {"label": "Rows with price", "value": _fmt_num(rows_with_price)},
            {"label": "COA rate", "value": _fmt_pct(coa_rate)},
            {"label": "Avg price", "value": _fmt_money(avg_price)},
            {"label": "Median price", "value": _fmt_money(med_price)},
        ]
        if date_min is not None and date_max is not None:
            metrics.append({"label": "Date range", "value": f"{date_min.date()} → {date_max.date()}"})
        if top_prodgrade is not None and top_prodgrade_n is not None:
            metrics.append({"label": "Top Product+Grade", "value": f"{top_prodgrade} (n={top_prodgrade_n:,})"})

        recs_md = """
**Recommendations**
- If a trace trends up/down, review **pricing**, **mix shifts**, and **discounting** over that period.
- Compare **With COA vs Without COA** at similar times/products to validate whether COA correlates with higher achieved prices.
- If some traces are sparse, consider grouping by **Product Type only** for more stable inference.
"""
        render_dir_expander_metrics("Chart 1", definitions_md, metrics, recs_md)

    # ======================
    # Chart 2
    # ======================
    with t2:
        st.markdown("### Chart 2: COA Price Premium by Grade")
        c_df = _apply_coa_selector(c_base, "coa_sel_chart2")

        if c_df.empty or "Grade" not in c_df.columns or "Price (CAD)" not in c_df.columns:
            st.info("No data available for Chart 2 under current filters.")
        else:
            price_df = c_df.dropna(subset=["Grade", "Price (CAD)"]).copy()
            agg_price = (
                price_df.groupby(["Grade", "COA Status"], dropna=False)
                .agg(
                    Avg_Price_CAD=("Price (CAD)", "mean"),
                    Sale_Count=(("Sale ID" if "Sale ID" in price_df.columns else "Price (CAD)"), "count"),
                )
                .reset_index()
            )

            if agg_price.empty:
                st.info("No Grade/COA combinations found for Chart 2.")
            else:
                grade_order = sorted(agg_price["Grade"].astype(str).unique().tolist())
                fig2 = px.bar(
                    agg_price,
                    x="Grade",
                    y="Avg_Price_CAD",
                    color="COA Status",
                    barmode="group",
                    category_orders={"Grade": grade_order},
                    hover_data=["Sale_Count"],
                    labels={"Avg_Price_CAD": "Average Price (CAD)"},
                    title="Average Price by Grade and COA Status",
                )
                fig2 = style_fig(fig2, height=520)
                st.plotly_chart(fig2, use_container_width=True, key=pkey("comp_chart2"))

        # DIR expander
        total_rows = int(len(c_df))
        coa_rate = float((c_df["COA Status"] == "With COA").mean() * 100) if ("COA Status" in c_df.columns and len(c_df) > 0) else None

        overall_with = None
        overall_without = None
        premium_abs = None
        premium_pct = None
        if "Price (CAD)" in c_df.columns and "COA Status" in c_df.columns:
            with_prices = c_df.dropna(subset=["Price (CAD)"])
            if not with_prices.empty:
                overall_with = float(with_prices.loc[with_prices["COA Status"] == "With COA", "Price (CAD)"].mean())
                overall_without = float(with_prices.loc[with_prices["COA Status"] == "No COA", "Price (CAD)"].mean())
                if np.isfinite(overall_with) and np.isfinite(overall_without):
                    premium_abs = overall_with - overall_without
                    premium_pct = (premium_abs / overall_without * 100) if overall_without != 0 else None

        best_grade = None
        best_premium = None
        if "agg_price" in locals() and not agg_price.empty:
            pv = agg_price.pivot_table(index="Grade", columns="COA Status", values="Avg_Price_CAD", aggfunc="first")
            if "With COA" in pv.columns and "No COA" in pv.columns:
                pv["Premium"] = pv["With COA"] - pv["No COA"]
                if pv["Premium"].notna().any():
                    best_grade = pv["Premium"].idxmax()
                    best_premium = float(pv.loc[best_grade, "Premium"])

        definitions_md = """
**What this chart shows**
- **Bar height** = average sale price (CAD).
- Grouped by **Grade** and split by **COA Status**.
- Use this to estimate a **COA premium** within each grade.
"""
        metrics = [
            {"label": "Rows in view", "value": _fmt_num(total_rows)},
            {"label": "COA rate", "value": _fmt_pct(coa_rate)},
            {"label": "Mean price (With COA)", "value": _fmt_money(overall_with)},
            {"label": "Mean price (No COA)", "value": _fmt_money(overall_without)},
            {"label": "COA premium (mean)", "value": _fmt_money(premium_abs), "delta": _fmt_pct(premium_pct)},
        ]
        if best_grade is not None:
            metrics.append({"label": "Largest premium grade", "value": f"{best_grade} ({_fmt_money(best_premium)})"})

        recs_md = """
**Recommendations**
- If premium is large for a grade, prioritize **COA completion** for that grade’s inventory.
- If premium is near-zero, validate whether the grade already signals quality strongly enough.
- Averages can be skewed—consider adding a **median** version later.
"""
        render_dir_expander_metrics("Chart 2", definitions_md, metrics, recs_md)

    # ======================
    # Chart 3
    # ======================
    with t3:
        st.markdown("### Chart 3: Average Days from Sale to Shipment (Country × Grade)")
        c_df = _apply_coa_selector(c_base, "coa_sel_chart3")

        if c_df.empty or "Country" not in c_df.columns or "Grade" not in c_df.columns:
            st.info("No data available for Chart 3 under current filters.")
        else:
            ship_df = c_df.copy()
            ship_df = ship_df.dropna(subset=["Days_to_Ship"])
            ship_df = ship_df[ship_df["Days_to_Ship"] >= 0]

            if ship_df.empty:
                st.info("No valid shipping intervals remain for Chart 3.")
            else:
                non_canada_mask = ship_df["Country"].astype(str).str.lower().ne("canada")
                no_permit_mask = ship_df["Export_Permit_Clean"].isna()
                removed = int((non_canada_mask & no_permit_mask).sum())
                ship_df_chart = ship_df[~(non_canada_mask & no_permit_mask)].copy()

                if removed > 0:
                    st.warning(f"{removed} export rows without permits were excluded from Chart 3.")

                if ship_df_chart.empty:
                    st.info("After excluding export-without-permit rows, no data remains for Chart 3.")
                else:
                    ship_df_chart["Country_display"] = ship_df_chart["Country"].astype(str)
                    ship_df_chart.loc[ship_df_chart["Country_display"].str.lower().eq("canada"), "Country_display"] = "Canada"

                    agg_ship = (
                        ship_df_chart.groupby(["Country_display", "Grade"], dropna=False)
                        .agg(
                            Avg_Days_to_Ship=("Days_to_Ship", "mean"),
                            Shipment_Count=(("Sale ID" if "Sale ID" in ship_df_chart.columns else "Days_to_Ship"), "count"),
                        )
                        .reset_index()
                    )

                    has_canada = agg_ship["Country_display"].str.lower().eq("canada").any()
                    others = sorted(agg_ship.loc[~agg_ship["Country_display"].str.lower().eq("canada"), "Country_display"].dropna().unique().tolist())
                    ordered_countries = (["Canada"] + others) if has_canada else others
                    grade_order = sorted(agg_ship["Grade"].dropna().astype(str).unique().tolist())

                    fig3 = px.bar(
                        agg_ship,
                        x="Country_display",
                        y="Avg_Days_to_Ship",
                        color="Grade",
                        barmode="group",
                        category_orders={"Country_display": ordered_countries, "Grade": grade_order},
                        hover_data=["Shipment_Count"],
                        title="Average Days to Ship by Country and Grade (exports without permits excluded)",
                        labels={"Avg_Days_to_Ship": "Average Days to Ship", "Country_display": "Country"},
                    )
                    fig3 = style_fig(fig3, height=560)
                    st.plotly_chart(fig3, use_container_width=True, key=pkey("comp_chart3"))

        # DIR expander
        row_count = int(len(ship_df_chart)) if "ship_df_chart" in locals() else 0
        dom_avg = None
        exp_avg = None
        if "ship_df_chart" in locals() and not ship_df_chart.empty:
            is_dom = ship_df_chart["Country_display"].astype(str).str.lower().eq("canada")
            dom_avg = float(ship_df_chart.loc[is_dom, "Days_to_Ship"].mean()) if is_dom.any() else None
            exp_avg = float(ship_df_chart.loc[~is_dom, "Days_to_Ship"].mean()) if (~is_dom).any() else None

        worst_country = None
        worst_days = None
        if "agg_ship" in locals() and "Country_display" in agg_ship.columns and not agg_ship.empty:
            tmp = agg_ship.groupby("Country_display", dropna=False)["Avg_Days_to_Ship"].mean()
            if not tmp.empty:
                worst_country = tmp.idxmax()
                worst_days = float(tmp.loc[worst_country])

        definitions_md = """
**What this chart shows**
- Average **Days_to_Ship** by **Country × Grade**.
- Excludes **exports missing a permit** to avoid mixing non-compliant shipping records.
"""
        metrics = [
            {"label": "Rows used", "value": _fmt_num(row_count)},
            {"label": "Excluded (no permit)", "value": _fmt_num(removed if "removed" in locals() else None)},
            {"label": "Avg ship days (Canada)", "value": _fmt_num(dom_avg)},
            {"label": "Avg ship days (Export)", "value": _fmt_num(exp_avg)},
        ]
        if worst_country is not None:
            metrics.append({"label": "Slowest country", "value": f"{worst_country} ({_fmt_num(worst_days)}d)"})

        recs_md = """
**Recommendations**
- If export shipping is slower, review **carrier choice**, **packaging workflow**, and **documentation lead time**.
- Prioritize fixes for the **slowest country** (largest payoff).
- If a specific grade ships slower, check for extra steps (COA creation, special handling).
"""
        render_dir_expander_metrics("Chart 3", definitions_md, metrics, recs_md)

    # ======================
    # Chart 4 (Ammolite preset bins)
    # ======================
    with t4:
        st.markdown("### Chart 4: COA Adoption by Price Bucket")
        c_df = _apply_coa_selector(c_base, "coa_sel_chart4")

        if c_df.empty or "Price (CAD)" not in c_df.columns:
            st.info("No data available for Chart 4 under current filters.")
        else:
            price_df = c_df.dropna(subset=["Price (CAD)"]).copy()
            if price_df.empty:
                st.info("No rows with valid prices remain for Chart 4.")
            else:
                def round_up(x: float, step: int) -> int:
                    return int(math.ceil(x / step) * step)

                # Ammolite “customer-intuitive” bins (10 bins)
                edges_base = [0, 250, 500, 1000, 2000, 5000, 10000, 20000, 30000, 50000]
                max_price = float(price_df["Price (CAD)"].max())
                step_for_cap = 1000 if max_price <= 100000 else 5000

                if not np.isfinite(max_price) or max_price <= 0:
                    st.info("Prices are missing or non-positive; cannot build bins.")
                else:
                    cap = round_up(max_price, step_for_cap)
                    if cap <= edges_base[-1]:
                        cap = edges_base[-1] + step_for_cap

                    edges = edges_base + [cap]  # 11 edges => 10 bins

                    price_df["PriceBin"] = pd.cut(
                        price_df["Price (CAD)"],
                        bins=edges,
                        include_lowest=True,
                        right=True
                    )

                    labels = []
                    for i in range(10):
                        low = int(edges[i])
                        high = int(edges[i + 1])
                        start = low if i == 0 else (low + 1)
                        labels.append(f"${start:,.0f} - ${high:,.0f}")

                    bin_categories = price_df["PriceBin"].cat.categories
                    label_map = {bin_categories[i]: labels[i] for i in range(len(bin_categories))}
                    price_df["PriceBinLabel"] = price_df["PriceBin"].map(label_map)

                    price_df["PriceBinLabel"] = pd.Categorical(
                        price_df["PriceBinLabel"],
                        categories=labels,
                        ordered=True
                    )

                    st.caption(f"Using Ammolite preset bins up to ${cap:,.0f} (max price ${max_price:,.0f}).")

                    grp = (
                        price_df.groupby(["PriceBinLabel", "COA Status"], dropna=False, observed=False)
                        .size()
                        .reset_index(name="Sale_Count")
                    )

                    if grp.empty:
                        st.info("No price bins could be formed for Chart 4.")
                    else:
                        ordered_labels = labels  # keep all bins even if empty

                        pivot = (
                            grp.pivot(index="PriceBinLabel", columns="COA Status", values="Sale_Count")
                            .reindex(ordered_labels)
                            .fillna(0)
                        )

                        with_coa = pivot["With COA"] if "With COA" in pivot.columns else 0
                        no_coa = pivot["No COA"] if "No COA" in pivot.columns else 0

                        pivot["With_COA_Count"] = with_coa
                        pivot["No_COA_Count"] = no_coa
                        pivot["Total_Count"] = pivot["With_COA_Count"] + pivot["No_COA_Count"]
                        pivot["COA_Rate"] = pivot["With_COA_Count"] / pivot["Total_Count"].replace(0, pd.NA)
                        pivot = pivot.reset_index()

                        grp["PriceBinLabel"] = pd.Categorical(grp["PriceBinLabel"], categories=ordered_labels, ordered=True)
                        grp = grp.sort_values("PriceBinLabel")

                        fig4 = go.Figure()
                        for status in sorted(grp["COA Status"].dropna().unique()):
                            d = grp[grp["COA Status"] == status]
                            fig4.add_bar(x=d["PriceBinLabel"].astype(str), y=d["Sale_Count"], name=status)

                        fig4.add_trace(
                            go.Scatter(
                                x=ordered_labels,
                                y=(pivot["COA_Rate"] * 100),
                                name="COA Adoption (%)",
                                mode="lines+markers",
                                yaxis="y2",
                            )
                        )

                        fig4.update_layout(
                            barmode="stack",
                            xaxis=dict(title="Price Bucket (CAD)"),
                            yaxis=dict(title="Number of Sales"),
                            yaxis2=dict(
                                title="COA Adoption (%)",
                                overlaying="y",
                                side="right",
                                range=[0, 100],
                            ),
                            title="COA Adoption and Sales Volume by Price Bucket",
                            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
                        )

                        fig4 = style_fig(fig4, height=560)
                        st.plotly_chart(fig4, use_container_width=True, key=pkey("comp_chart4"))

        # DIR expander
        total_sales = int(price_df.shape[0]) if "price_df" in locals() else 0
        overall_coa_rate = None
        if "pivot" in locals() and not pivot.empty and "With_COA_Count" in pivot.columns and "Total_Count" in pivot.columns:
            tot_with = float(pivot["With_COA_Count"].sum())
            tot_total = float(pivot["Total_Count"].sum())
            overall_coa_rate = (tot_with / tot_total * 100) if tot_total > 0 else None

        most_volume_bin = None
        most_volume_n = None
        best_bin = None
        best_rate = None
        worst_bin = None
        worst_rate = None
        if "pivot" in locals() and not pivot.empty and "Total_Count" in pivot.columns and "COA_Rate" in pivot.columns:
            pv2 = pivot.copy()
            pv2["COA_Rate_pct"] = pv2["COA_Rate"] * 100
            if pv2["Total_Count"].notna().any():
                idx = pv2["Total_Count"].idxmax()
                most_volume_bin = str(pv2.loc[idx, "PriceBinLabel"])
                most_volume_n = int(pv2.loc[idx, "Total_Count"])
            if pv2["COA_Rate_pct"].notna().any():
                best_idx = pv2["COA_Rate_pct"].idxmax()
                worst_idx = pv2["COA_Rate_pct"].idxmin()
                best_bin = str(pv2.loc[best_idx, "PriceBinLabel"])
                best_rate = float(pv2.loc[best_idx, "COA_Rate_pct"])
                worst_bin = str(pv2.loc[worst_idx, "PriceBinLabel"])
                worst_rate = float(pv2.loc[worst_idx, "COA_Rate_pct"])

        definitions_md = """
**What this chart shows**
- **Stacked bars**: sales count per price bucket split by **COA Status**.
- **Line**: **COA Adoption (%)** = With COA / Total within that bucket.
- Buckets use your **Ammolite preset** ranges + a dynamic top cap.
"""
        metrics = [
            {"label": "Sales (priced rows)", "value": _fmt_num(total_sales)},
            {"label": "Overall COA adoption", "value": _fmt_pct(overall_coa_rate)},
        ]
        if most_volume_bin is not None:
            metrics.append({"label": "Highest volume bucket", "value": most_volume_bin})
            metrics.append({"label": "Volume in top bucket", "value": _fmt_num(most_volume_n)})
        if best_bin is not None:
            metrics.append({"label": "Best adoption bucket", "value": best_bin, "delta": _fmt_pct(best_rate)})
        if worst_bin is not None:
            metrics.append({"label": "Worst adoption bucket", "value": worst_bin, "delta": _fmt_pct(worst_rate)})

        recs_md = """
**Recommendations**
- If adoption drops at higher prices, enforce “**COA required above $X**”.
- If adoption is low at low prices, consider **batch COA workflows** to reduce overhead.
- Prioritize improvements in the **highest volume bucket** for maximum impact.
"""
        render_dir_expander_metrics("Chart 4", definitions_md, metrics, recs_md)

    # ======================
    # Chart 5
    # ======================
    with t5:
        st.markdown("### Chart 5: Shipping Delay Distribution by Compliance Group")
        c_df = _apply_coa_selector(c_base, "coa_sel_chart5")

        if c_df.empty or "Country" not in c_df.columns:
            st.info("No data available for Chart 5 under current filters.")
        else:
            ship_df = c_df.copy()
            ship_df = ship_df.dropna(subset=["Days_to_Ship"])
            ship_df = ship_df[ship_df["Days_to_Ship"] >= 0]

            if ship_df.empty:
                st.info("No valid shipping intervals remain for Chart 5.")
            else:
                non_canada_mask = ship_df["Country"].astype(str).str.lower().ne("canada")
                no_permit_mask = ship_df["Export_Permit_Clean"].isna()
                invalid_export_df = ship_df[non_canada_mask & no_permit_mask]

                excluded_no_permit = int(len(invalid_export_df))
                if excluded_no_permit > 0:
                    st.warning(f"{excluded_no_permit} export rows without permits were excluded from the violin plot.")
                    with st.expander("Show excluded rows (export without permit)"):
                        cols = [c for c in ["Sale ID", "Date", "Shipped Date", "Days_to_Ship", "Product Type", "Grade", "Country", "Customer Name", "Export Permit (PDF link)"] if c in invalid_export_df.columns]
                        st.dataframe(invalid_export_df[cols].head(200), use_container_width=True)

                ship_df_chart = ship_df[~(non_canada_mask & no_permit_mask)].copy()
                if ship_df_chart.empty:
                    st.info("After exclusions, no data remains for Chart 5.")
                else:
                    ship_df_chart["Country_display"] = ship_df_chart["Country"].astype(str)
                    ship_df_chart.loc[ship_df_chart["Country_display"].str.lower().eq("canada"), "Country_display"] = "Canada"

                    is_domestic = ship_df_chart["Country_display"].str.lower().eq("canada")
                    has_coa = ship_df_chart["COA Status"].eq("With COA")
                    has_permit = ship_df_chart["Export_Permit_Clean"].notna() | is_domestic

                    ship_df_chart["Compliance_Group"] = "Domestic - No COA"
                    ship_df_chart.loc[is_domestic & has_coa, "Compliance_Group"] = "Domestic - With COA"
                    ship_df_chart.loc[~is_domestic & has_coa & has_permit, "Compliance_Group"] = "Export - With COA & Permit"
                    ship_df_chart.loc[~is_domestic & ~has_coa & has_permit, "Compliance_Group"] = "Export - No COA & Permit"

                    possible_order = [
                        "Domestic - No COA",
                        "Domestic - With COA",
                        "Export - No COA & Permit",
                        "Export - With COA & Permit",
                    ]
                    present_groups = [g for g in possible_order if g in ship_df_chart["Compliance_Group"].unique()]
                    ship_df_chart["Compliance_Group"] = pd.Categorical(
                        ship_df_chart["Compliance_Group"],
                        categories=present_groups,
                        ordered=True,
                    )

                    fig5 = px.violin(
                        ship_df_chart,
                        x="Compliance_Group",
                        y="Days_to_Ship",
                        color="Compliance_Group",
                        box=True,
                        points="all",
                        title="Shipping Delay Distribution by Compliance Group",
                        labels={"Days_to_Ship": "Days from Sale to Shipment"},
                    )
                    fig5.update_layout(xaxis_tickangle=-20)
                    fig5 = style_fig(fig5, height=560)
                    st.plotly_chart(fig5, use_container_width=True, key=pkey("comp_chart5"))

        # DIR expander
        count_rows = int(len(ship_df_chart)) if "ship_df_chart" in locals() else 0
        iqr = None
        fastest_group = None
        fastest_med = None
        slowest_group = None
        slowest_med = None

        if "ship_df_chart" in locals() and not ship_df_chart.empty:
            q25 = float(ship_df_chart["Days_to_Ship"].quantile(0.25))
            q75 = float(ship_df_chart["Days_to_Ship"].quantile(0.75))
            iqr = q75 - q25

            med = ship_df_chart.groupby("Compliance_Group")["Days_to_Ship"].median().sort_values()
            if not med.empty:
                fastest_group = str(med.index[0])
                fastest_med = float(med.iloc[0])
                slowest_group = str(med.index[-1])
                slowest_med = float(med.iloc[-1])

        definitions_md = """
**What this chart shows**
- Distribution of **Days_to_Ship** by **Compliance_Group**.
- “Export without permit” rows are excluded (export groups reflect permit-present records).
- Violin width ≈ density; the **box** shows quartiles.
"""
        metrics = [
            {"label": "Rows used", "value": _fmt_num(count_rows)},
            {"label": "Excluded (no permit)", "value": _fmt_num(excluded_no_permit if "excluded_no_permit" in locals() else None)},
            {"label": "IQR (days)", "value": _fmt_num(iqr)},
        ]
        if fastest_group is not None:
            metrics.append({"label": "Fastest median group", "value": fastest_group, "delta": f"{_fmt_num(fastest_med)}d"})
        if slowest_group is not None:
            metrics.append({"label": "Slowest median group", "value": slowest_group, "delta": f"{_fmt_num(slowest_med)}d"})

        recs_md = """
**Recommendations**
- If export groups have higher median + wider spread, tighten **documentation readiness** and **carrier SLAs**.
- If “Domestic - With COA” is slower than “Domestic - No COA”, COA creation may be gating fulfillment—consider **pre-generating COAs**.
- Target groups with the widest spread for **variance reduction** (standardize steps).
"""
        render_dir_expander_metrics("Chart 5", definitions_md, metrics, recs_md)

    # ======================
    # Chart 6
    # ======================
    with t6:
        st.markdown("### Chart 6: Compliance Score vs Average Order Value (Domestic vs Export)")
        c_df = _apply_coa_selector(c_base, "coa_sel_chart6")

        if c_df.empty or "Country" not in c_df.columns or "Price (CAD)" not in c_df.columns:
            st.info("No data available for Chart 6 under current filters.")
        else:
            comp_df = c_df.dropna(subset=["Price (CAD)"]).copy()

            country_str = comp_df["Country"].astype(str)
            is_domestic = country_str.str.lower().eq("canada")
            comp_df["Market_Type"] = np.where(is_domestic, "Domestic", "Export")

            has_coa = comp_df["COA Status"].eq("With COA")
            has_permit = comp_df["Export_Permit_Clean"].notna()

            comp_df["Compliance_Score"] = 0
            comp_df.loc[is_domestic & has_coa, "Compliance_Score"] = 2

            exp_mask = ~is_domestic
            comp_df.loc[exp_mask & has_coa & has_permit, "Compliance_Score"] = 2
            partial_mask = exp_mask & ((has_coa & ~has_permit) | (~has_coa & has_permit))
            comp_df.loc[partial_mask, "Compliance_Score"] = 1

            score_label_map = {
                0: "0 - No COA / No Permit",
                1: "1 - Partial Compliance",
                2: "2 - Fully Compliant",
            }
            comp_df["Compliance_Score_Label"] = comp_df["Compliance_Score"].map(score_label_map)

            agg_comp = (
                comp_df.groupby(["Market_Type", "Compliance_Score", "Compliance_Score_Label"], dropna=False)
                .agg(
                    Avg_Price_CAD=("Price (CAD)", "mean"),
                    Order_Count=(("Sale ID" if "Sale ID" in comp_df.columns else "Price (CAD)"), "count"),
                )
                .reset_index()
            )

            if agg_comp.empty:
                st.info("No combinations available for Chart 6 under current filters.")
            else:
                score_order = [
                    "0 - No COA / No Permit",
                    "1 - Partial Compliance",
                    "2 - Fully Compliant",
                ]
                market_order = ["Domestic", "Export"]

                fig6 = px.bar(
                    agg_comp,
                    x="Compliance_Score_Label",
                    y="Avg_Price_CAD",
                    color="Market_Type",
                    category_orders={"Compliance_Score_Label": score_order, "Market_Type": market_order},
                    barmode="group",
                    hover_data=["Order_Count"],
                    labels={
                        "Compliance_Score_Label": "Compliance Score",
                        "Avg_Price_CAD": "Average Order Value (CAD)",
                        "Market_Type": "Market",
                    },
                    title="Average Order Value by Compliance Score and Market Type",
                )
                fig6 = style_fig(fig6, height=560)
                st.plotly_chart(fig6, use_container_width=True, key=pkey("comp_chart6"))

        # DIR expander
        rows_used = int(len(comp_df)) if "comp_df" in locals() else 0

        def _get_avg(market, score):
            if "agg_comp" not in locals() or agg_comp.empty:
                return None
            sub = agg_comp[(agg_comp["Market_Type"] == market) & (agg_comp["Compliance_Score"] == score)]
            return float(sub["Avg_Price_CAD"].iloc[0]) if len(sub) else None

        d0, d2 = _get_avg("Domestic", 0), _get_avg("Domestic", 2)
        e0, e2 = _get_avg("Export", 0), _get_avg("Export", 2)

        dom_uplift_abs = (d2 - d0) if (d0 is not None and d2 is not None) else None
        dom_uplift_pct = ((d2 - d0) / d0 * 100) if (d0 is not None and d2 is not None and d0 != 0) else None
        exp_uplift_abs = (e2 - e0) if (e0 is not None and e2 is not None) else None
        exp_uplift_pct = ((e2 - e0) / e0 * 100) if (e0 is not None and e2 is not None and e0 != 0) else None

        best_combo = None
        if "agg_comp" in locals() and not agg_comp.empty:
            idx = agg_comp["Avg_Price_CAD"].idxmax()
            best_combo = (str(agg_comp.loc[idx, "Market_Type"]), int(agg_comp.loc[idx, "Compliance_Score"]), float(agg_comp.loc[idx, "Avg_Price_CAD"]))

        definitions_md = """
**What this chart shows**
- **Compliance_Score** (0/1/2) vs **Average Order Value**, split by **Domestic** and **Export**.
- Score logic:
  - **Domestic**: COA drives compliance.
  - **Export**: COA + Permit = fully compliant; one of them = partial.
"""
        metrics = [
            {"label": "Rows used", "value": _fmt_num(rows_used)},
            {"label": "Domestic: Score2 vs 0", "value": _fmt_money(dom_uplift_abs), "delta": _fmt_pct(dom_uplift_pct)},
            {"label": "Export: Score2 vs 0", "value": _fmt_money(exp_uplift_abs), "delta": _fmt_pct(exp_uplift_pct)},
        ]
        if best_combo is not None:
            metrics.append({"label": "Highest AOV combo", "value": f"{best_combo[0]} (Score {best_combo[1]})", "delta": _fmt_money(best_combo[2])})

        recs_md = """
**Recommendations**
- If Score 2 orders have higher value, treat compliance as a **revenue lever**, not just paperwork.
- For exports, standardize a “**permit + COA checklist**” to move orders from Score 0/1 → 2.
- If Score 1 ≈ Score 2, focus on whichever component (COA vs permit) is cheaper/faster to improve.
"""
        render_dir_expander_metrics("Chart 6", definitions_md, metrics, recs_md)

    # ======================
    # Chart 7
    # ======================
    with t7:
        st.markdown("### Chart 7: COA Coverage by Product Type")
        c_df = _apply_coa_selector(c_base, "coa_sel_chart7")

        if c_df.empty or "Product Type" not in c_df.columns:
            st.info("No data available for Chart 7 under current filters.")
        else:
            df7 = c_df.copy()
            df7["Has_Valid_COA"] = df7["COA Status"].eq("With COA")

            agg7 = (
                df7.groupby("Product Type", dropna=False)
                .agg(
                    COA_Rate=("Has_Valid_COA", "mean"),
                    Order_Count=(("Sale ID" if "Sale ID" in df7.columns else "Has_Valid_COA"), "count"),
                )
                .reset_index()
                .sort_values("COA_Rate", ascending=False)
            )

            if agg7.empty:
                st.info("No product types available for Chart 7.")
            else:
                fig7 = px.bar(
                    agg7,
                    x="Product Type",
                    y="COA_Rate",
                    hover_data=["Order_Count"],
                    text_auto=".0%",
                    title="COA Coverage Rate by Product Type",
                    labels={"COA_Rate": "COA Coverage Rate"},
                )
                fig7.update_layout(yaxis_tickformat=".0%")
                fig7 = style_fig(fig7, height=560)
                st.plotly_chart(fig7, use_container_width=True, key=pkey("comp_chart7"))

        # DIR expander
        overall_rate = float(df7["Has_Valid_COA"].mean() * 100) if ("df7" in locals() and not df7.empty and "Has_Valid_COA" in df7.columns) else None
        pt_count = int(df7["Product Type"].nunique()) if ("df7" in locals() and "Product Type" in df7.columns) else None

        top_pt = None
        bottom_pt = None
        if "agg7" in locals() and not agg7.empty:
            top = agg7.iloc[0]
            bot = agg7.iloc[-1]
            top_pt = (str(top["Product Type"]), float(top["COA_Rate"] * 100), int(top["Order_Count"]))
            bottom_pt = (str(bot["Product Type"]), float(bot["COA_Rate"] * 100), int(bot["Order_Count"]))

        definitions_md = """
**What this chart shows**
- **COA coverage rate** by **Product Type**.
- Coverage is based on **valid COA status** (With COA vs No COA).
"""
        metrics = [
            {"label": "Overall coverage", "value": _fmt_pct(overall_rate)},
            {"label": "Product types", "value": _fmt_num(pt_count)},
        ]
        if top_pt is not None:
            metrics.append({"label": "Highest coverage", "value": top_pt[0], "delta": f"{_fmt_pct(top_pt[1])} (n={top_pt[2]:,})"})
        if bottom_pt is not None:
            metrics.append({"label": "Lowest coverage", "value": bottom_pt[0], "delta": f"{_fmt_pct(bottom_pt[1])} (n={bottom_pt[2]:,})"})

        recs_md = """
**Recommendations**
- If a product type has low coverage but high volume, prioritize **COA workflow improvements** there first.
- If low coverage types are niche/low volume, consider “**COA optional under $X**”.
- Track coverage over time to confirm process changes are improving adoption.
"""
        render_dir_expander_metrics("Chart 7", definitions_md, metrics, recs_md)
# -----------------------------
# TAB: All Data
# -----------------------------
with tab_data:
    st.subheader("All Filtered Data")
    st.markdown("Full dataset after applying filters. Download for extra analysis if you need.")

    subset = f.copy()
    subset = subset.loc[:, ~subset.columns.duplicated()]
    st.dataframe(subset.head(max_rows), use_container_width=True)

    st.download_button(
        "Download filtered dataset (CSV)",
        data=subset.to_csv(index=False).encode("utf-8"),
        file_name="ammolite_filtered_full.csv",
        mime="text/csv",
        key="dl_all",
    )
