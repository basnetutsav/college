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
# TAB: Price Drivers / Visualization (REPLACED to match your 5-tab layout + 9 visuals)
# -----------------------------
with tab_price:
    st.subheader("Price Drivers / Visualization")

    p_df = f.copy()

    # Use Net Sales if available (best “revenue after discount”), else fallback
    if safe_col(p_df, "Net Sales"):
        revenue_col = "Net Sales"
    elif safe_col(p_df, "Price (CAD)"):
        revenue_col = "Price (CAD)"
    else:
        revenue_col = metric_col  # last resort

    price_col = revenue_col  # “Average Price (Unit Value)” in your screenshots

    # Most recent year in the filtered view (matches your screenshots showing 2025)
    year_pick = int(p_df["Year"].dropna().max()) if safe_col(p_df, "Year") and p_df["Year"].notna().any() else None
    p_year = p_df[p_df["Year"] == year_pick].copy() if year_pick is not None else p_df.copy()

    # 5 Tabs (exact structure you requested)
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
        else:
            st.info("Missing required columns for this chart (need Product Type, Grade, and a price column).")

    # -----------------------------
    # TAB 2 (2 visuals)
    # Sales Performance by Dominant Color
    # -----------------------------
  with t2:
    import plotly.colors as pc

    # Main title (like your screenshot)
    st.markdown("## Sales Performance by Dominant Color")

    if safe_col(p_df, "Dominant Color") and safe_col(p_df, revenue_col) and safe_col(p_df, price_col):
        tmp = p_df.dropna(subset=["Dominant Color"]).copy()

        dom = (
            tmp.groupby("Dominant Color", as_index=False)
            .agg(
                Total_Revenue=(revenue_col, "sum"),
                Avg_Price=(price_col, "mean"),
            )
        )

        # Sort like your screenshot: Revenue chart desc, Avg Price chart desc
        dom_rev = dom.sort_values("Total_Revenue", ascending=False).reset_index(drop=True)
        dom_avg = dom.sort_values("Avg_Price", ascending=False).reset_index(drop=True)

        # Build nice gradient colors (same style look)
        def _grad_colors(n, scale_name="Viridis"):
            if n <= 1:
                return ["#4c78a8"]
            pts = np.linspace(0.05, 0.95, n)
            return pc.sample_colorscale(scale_name, pts)

        c1, c2 = st.columns(2)

        # -----------------------------
        # LEFT: Total Revenue
        # -----------------------------
        with c1:
            st.markdown("### Total Sales Value (Revenue) by Dominant Color")

            colors1 = _grad_colors(len(dom_rev), "Viridis")
            fig1 = go.Figure(
                data=[
                    go.Bar(
                        x=dom_rev["Dominant Color"],
                        y=dom_rev["Total_Revenue"],
                        marker=dict(color=colors1),
                    )
                ]
            )
            fig1.update_layout(
                title="Total Revenue by Dominant Color",
                xaxis_title="Dominant Color",
                yaxis_title="Total Sales Value (CAD)",
            )
            fig1.update_xaxes(tickangle=-60)
            fig1.update_yaxes(tickprefix="$", tickformat="~s")  # shows $600k style
            fig1 = style_fig(fig1, height=470)
            st.plotly_chart(fig1, use_container_width=True, key=pkey("pd_dom_rev"))

        # -----------------------------
        # RIGHT: Average Price
        # -----------------------------
        with c2:
            st.markdown("### Average Price (Unit Value) by Dominant Color")

            colors2 = _grad_colors(len(dom_avg), "Plasma")
            fig2 = go.Figure(
                data=[
                    go.Bar(
                        x=dom_avg["Dominant Color"],
                        y=dom_avg["Avg_Price"],
                        marker=dict(color=colors2),
                    )
                ]
            )
            fig2.update_layout(
                title="Average Price by Dominant Color",
                xaxis_title="Dominant Color",
                yaxis_title="Average Price (CAD)",
            )
            fig2.update_xaxes(tickangle=-60)
            fig2.update_yaxes(tickprefix="$", tickformat="~s")
            fig2 = style_fig(fig2, height=470)
            st.plotly_chart(fig2, use_container_width=True, key=pkey("pd_dom_avg"))

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
# TAB: Compliance (upgrade)
# -----------------------------
with tab_compliance:
    st.subheader("Compliance – COA & Export Permits")
    c_df = f.copy()

    c_tabs = st.tabs(["COA Coverage", "Export Permits", "Country Risk Bubble", "Data"])

    with c_tabs[0]:
        coa_counts = c_df.groupby("Has COA", as_index=False)["OrderCount"].sum().rename(columns={"OrderCount": "Count"})
        coa_counts["Status"] = coa_counts["Has COA"].map({True: "Has COA", False: "Missing COA"})

        fig = px.pie(coa_counts, names="Status", values="Count", title="COA Coverage – All Orders", hole=0.35)
        fig = style_fig(fig, height=430)
        st.plotly_chart(fig, use_container_width=True, key=pkey("coa_pie"))

        coa_country = (
            c_df.groupby("Country", as_index=False)["Has COA"].mean()
            .rename(columns={"Has COA": "COA Rate"})
            .sort_values("COA Rate", ascending=False)
            .head(12)
        )
        fig2 = px.bar(coa_country, x="Country", y="COA Rate", title="Top Countries – COA Coverage Rate", text_auto=".0%")
        fig2.update_layout(yaxis_tickformat=".0%")
        fig2 = style_fig(fig2, height=430)
        st.plotly_chart(fig2, use_container_width=True, key=pkey("coa_rate"))

    with c_tabs[1]:
        export_df = c_df[c_df["Is Export"]].copy()
        if export_df.empty:
            st.info("No export shipments in the current filters.")
        else:
            permit_counts = export_df.groupby("Has Export Permit", as_index=False)["OrderCount"].sum().rename(columns={"OrderCount": "Count"})
            permit_counts["Status"] = permit_counts["Has Export Permit"].map({True: "Compliant (Has Permit)", False: "Missing Permit"})
            fig = px.bar(permit_counts, x="Status", y="Count", title="Export Orders – Permit Status", text_auto=True)
            fig.update_layout(xaxis_title="", yaxis_title="Orders")
            fig = style_fig(fig, height=420)
            st.plotly_chart(fig, use_container_width=True, key=pkey("perm_bar"))

            missing = export_df[~export_df["Has Export Permit"]]
            if not missing.empty:
                miss_by_country = (
                    missing.groupby("Country", as_index=False)["OrderCount"].sum()
                    .rename(columns={"OrderCount": "Missing Permit Orders"})
                    .sort_values("Missing Permit Orders", ascending=False)
                )
                st.markdown("#### Missing Permits by Country")
                st.dataframe(miss_by_country, use_container_width=True)
            else:
                st.success("All export orders have permits recorded in this view.")

    with c_tabs[2]:
        export_df = c_df[c_df["Is Export"]].copy()
        if export_df.empty:
            st.info("No export shipments in the current filters.")
        else:
            risk = (
                export_df.groupby("Country", as_index=False)
                .agg(
                    ExportOrders=("OrderCount", "sum"),
                    MissingRate=("Has Export Permit", lambda s: 1 - float(s.mean()) if len(s) else 0),
                    ExportNetSales=("Net Sales", "sum"),
                )
            )
            risk = risk[risk["ExportOrders"] > 0].copy()
            fig = px.scatter(
                risk,
                x="ExportOrders",
                y="MissingRate",
                size="ExportNetSales",
                hover_name="Country",
                title="Country Risk Bubble (exports)",
            )
            fig.update_layout(xaxis_title="Export Orders", yaxis_title="Missing Permit Rate", yaxis_tickformat=".0%")
            fig = style_fig(fig, height=480)
            st.plotly_chart(fig, use_container_width=True, key=pkey("risk_bubble"))

    with c_tabs[3]:
        cols = ["Sale ID", "Date", "Country", "Channel", "Is Export", "Has COA", "Has Export Permit", metric_col, "Net Sales"]
        cols = [c for c in cols if c in c_df.columns]
        subset = c_df[cols].copy()
        subset = subset.loc[:, ~subset.columns.duplicated()]
        st.dataframe(subset.head(max_rows), use_container_width=True)
        st.download_button(
            "Download compliance subset (CSV)",
            data=subset.to_csv(index=False).encode("utf-8"),
            file_name="compliance_subset.csv",
            mime="text/csv",
            key="dl_comp",
        )

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
