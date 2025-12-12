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
    html, body, [class*="css"] { font-size: 0.95rem !important; }
    .block-container { padding-top: 0.8rem; padding-bottom: 2.0rem; max-width: 1550px; }
    div[data-testid="column"] { padding-left: 0.40rem; padding-right: 0.40rem; }
    [data-testid="metric-container"] { padding: 0.70rem 0.85rem !important; border-radius: 14px !important; }
    [data-testid="metric-container"] [data-testid="stMetricValue"] {
        font-size: 1.55rem !important;
        overflow: visible !important;
        text-overflow: clip !important;
        white-space: normal !important;
        line-height: 1.2 !important;
    }
    .stTabs [data-baseweb="tab"] { font-size: 0.95rem; }
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
    fig.update_layout(
        height=height,
        margin=dict(l=10, r=10, t=55, b=40),
        legend=dict(font=dict(size=11), orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        hoverlabel=dict(font_size=11),
        xaxis=dict(title_font=dict(size=13), tickfont=dict(size=11), automargin=True),
        yaxis=dict(title_font=dict(size=13), tickfont=dict(size=11), automargin=True),
    )
    fig.update_traces(hovertemplate=None)
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
                # older pandas: no encoding_errors
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
        df["Has Export Permit"] = df["Export Permit (PDF link)"].astype(str).str.strip().ne("") & df["Export Permit (PDF link)"].notna()
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
        st.metric(metric_label, fmt_int(cur_total_metric),
                  delta=(None if not np.isfinite(prev_total_metric) else f"{int(cur_total_metric - prev_total_metric):,}"))
    else:
        st.metric(metric_label, fmt_money(cur_total_metric),
                  delta=(None if not np.isfinite(prev_total_metric) else fmt_money(cur_total_metric - prev_total_metric)))

with k2:
    st.metric("Total Net Sales", fmt_money(cur_total_net),
              delta=(None if not np.isfinite(prev_total_net) else fmt_money(cur_total_net - prev_total_net)))

with k3:
    st.metric("Total Orders", fmt_int(cur_orders),
              delta=(None if not np.isfinite(prev_orders) else f"{int(cur_orders - prev_orders):,}"))

with k4:
    st.metric("Unique Customers", fmt_int(cur_unique),
              delta=(None if not np.isfinite(prev_unique) else f"{int(cur_unique - prev_unique):,}"))

with k5:
    st.metric("Consigned Share", f"{cur_cons_share*100:,.1f}%",
              delta=(None if not np.isfinite(prev_cons_share) else f"{(cur_cons_share - prev_cons_share)*100:,.1f}%"))

with k6:
    if np.isfinite(cur_avg_ship):
        st.metric("Avg Days to Ship", f"{cur_avg_ship:,.1f}",
                  delta=(None if not np.isfinite(prev_avg_ship) else f"{(cur_avg_ship - prev_avg_ship):,.1f}"))
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
            fig.add_trace(go.Scatter(x=pareto["Country"], y=pareto["CumShare"], name="Cumulative share", yaxis="y2", mode="lines+markers"))
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
            by_prod = f.groupby("Product Type", as_index=False)[metric_col].sum().sort_values(metric_col, ascending=False).head(12)
            fig = px.bar(by_prod, x=metric_col, y="Product Type", orientation="h", text_auto=".2s", title=f"Top Product Types by {metric_label}")
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
# TAB: Price Drivers (more advanced)
# -----------------------------
with tab_price:
    st.subheader("Price Drivers – Grade, Colour, Size")

    p_df = f.copy()

    p_tabs = st.tabs(["Driver Explorer", "Distributions", "Heatmaps", "Correlations", "Data"])

    # --- Driver Explorer
    with p_tabs[0]:
        st.markdown("#### Driver Explorer (choose a driver → see impact on Net Sales)")
        driver_options = []
        for col in ["Grade", "Finish", "Product Type", "Dominant Color", "Channel", "Country", "Customer Type", "Ownership"]:
            if safe_col(p_df, col):
                driver_options.append(col)

        driver = st.selectbox("Driver", options=driver_options if driver_options else ["(none)"], key="pd_driver")
        agg = st.selectbox("Aggregation", ["Median", "Mean"], key="pd_agg")

        if driver != "(none)":
            g = p_df.groupby(driver, as_index=False).agg(
                Orders=("Sale ID", "count") if safe_col(p_df, "Sale ID") else ("OrderCount", "sum"),
                NetSales=("Net Sales", "sum"),
                Avg=("Net Sales", "mean"),
                Med=("Net Sales", "median"),
            )

            g["Chosen"] = g["Med"] if agg == "Median" else g["Avg"]
            g = g.sort_values("Chosen", ascending=False).head(20)

            c1, c2 = st.columns([1.2, 1])

            with c1:
                fig = px.bar(
                    g,
                    x="Chosen",
                    y=driver,
                    orientation="h",
                    title=f"{agg} Net Sales by {driver} (Top 20)",
                    hover_data={"Orders": True, "NetSales": ":,.0f", "Avg": ":,.0f", "Med": ":,.0f"},
                )
                fig.update_layout(xaxis_title=f"{agg} Net Sales (CAD)", yaxis_title="")
                fig = style_fig(fig, height=470)
                st.plotly_chart(fig, use_container_width=True, key=pkey("pd_driver_bar"))

            with c2:
                # Density view for numeric drivers: Color Count, Area, Weight
                numeric_driver = st.selectbox(
                    "Numeric driver (optional)",
                    options=[x for x in ["Color Count (#)", "weight", "Area (mm²)", "Price per mm²"] if safe_col(p_df, x)],
                    index=0 if safe_col(p_df, "Color Count (#)") else 0,
                    key="pd_num_driver",
                )
                if numeric_driver and safe_col(p_df, numeric_driver) and p_df[numeric_driver].notna().any():
                    tmp = p_df.dropna(subset=[numeric_driver, "Net Sales"]).copy()
                    fig2 = px.density_heatmap(
                        tmp,
                        x=numeric_driver,
                        y="Net Sales",
                        nbinsx=30,
                        nbinsy=30,
                        title=f"Density: Net Sales vs {numeric_driver}",
                    )
                    fig2.update_layout(xaxis_title=numeric_driver, yaxis_title="Net Sales (CAD)")
                    fig2 = style_fig(fig2, height=470)
                    st.plotly_chart(fig2, use_container_width=True, key=pkey("pd_density"))
                else:
                    st.info("No numeric driver data available for the selected field.")

    # --- Distributions
    with p_tabs[1]:
        st.markdown("#### Distributions (better than simple boxplots)")
        dist_by = st.selectbox(
            "Group by",
            options=[c for c in ["Grade", "Finish", "Product Type", "Channel", "Ownership"] if safe_col(p_df, c)],
            key="pd_dist_by",
        )

        if dist_by:
            tmp = p_df.dropna(subset=["Net Sales"]).copy()
            # Violin (shows full shape) + points
            fig = px.violin(
                tmp,
                x=dist_by,
                y="Net Sales",
                box=True,
                points="all",
                title=f"Net Sales Distribution by {dist_by} (Violin)",
            )
            fig.update_layout(xaxis_title=dist_by, yaxis_title="Net Sales (CAD)")
            fig = style_fig(fig, height=470)
            st.plotly_chart(fig, use_container_width=True, key=pkey("pd_violin"))

            # Histogram split by same group (top 6)
            top_groups = tmp[dist_by].value_counts().head(6).index.tolist()
            tmp2 = tmp[tmp[dist_by].isin(top_groups)].copy()
            fig2 = px.histogram(
                tmp2,
                x="Net Sales",
                color=dist_by,
                nbins=45,
                title=f"Histogram of Net Sales (Top {len(top_groups)} {dist_by})",
            )
            fig2.update_layout(xaxis_title="Net Sales (CAD)", yaxis_title="Orders")
            fig2 = style_fig(fig2, height=430)
            st.plotly_chart(fig2, use_container_width=True, key=pkey("pd_hist"))

    # --- Heatmaps
    with p_tabs[2]:
        st.markdown("#### Heatmaps (Avg/Median + Order Volume toggle)")
        row = st.selectbox("Rows", options=[c for c in ["Grade", "Finish", "Product Type", "Channel"] if safe_col(p_df, c)], key="pd_hm_row")
        col = st.selectbox("Columns", options=[c for c in ["Finish", "Grade", "Channel", "Customer Type"] if safe_col(p_df, c)], key="pd_hm_col")
        measure = st.selectbox("Cell value", ["Average Net Sales", "Median Net Sales", "Order Count"], key="pd_hm_val")

        if row and col and row != col:
            if measure == "Average Net Sales":
                pv = p_df.pivot_table(index=row, columns=col, values="Net Sales", aggfunc="mean", fill_value=0).round(0)
                label = "Avg Net Sales (CAD)"
            elif measure == "Median Net Sales":
                pv = p_df.pivot_table(index=row, columns=col, values="Net Sales", aggfunc="median", fill_value=0).round(0)
                label = "Median Net Sales (CAD)"
            else:
                base = "Sale ID" if safe_col(p_df, "Sale ID") else "OrderCount"
                pv = p_df.pivot_table(index=row, columns=col, values=base, aggfunc="count", fill_value=0)
                label = "Order Count"

            if not pv.empty:
                # limit size for readability
                max_rows_hm = st.slider("Max rows in heatmap", 5, 35, 20, key="pd_hm_maxr")
                max_cols_hm = st.slider("Max columns in heatmap", 5, 35, 15, key="pd_hm_maxc")

                pv2 = pv.copy()
                pv2 = pv2.iloc[:max_rows_hm, :max_cols_hm]

                hm = px.imshow(
                    pv2,
                    aspect="auto",
                    labels=dict(x=col, y=row, color=label),
                    title=f"{label} Heatmap – {row} × {col}",
                )
                hm = style_fig(hm, height=500)
                st.plotly_chart(hm, use_container_width=True, key=pkey("pd_hm"))
            else:
                st.info("Heatmap is empty for current selection.")
        else:
            st.info("Pick different fields for Rows and Columns.")

    # --- Correlations
    with p_tabs[3]:
        st.markdown("#### Correlation (numeric drivers ↔ pricing)")
        num_candidates = [c for c in ["Net Sales", "Total Collected", "Discount (CAD)", "Shipping (CAD)",
                                     "Taxes Collected (CAD)", "Color Count (#)", "length", "width", "weight",
                                     "Area (mm²)", "Price per mm²", "Days to Ship"] if safe_col(p_df, c)]
        tmp = p_df[num_candidates].copy()
        tmp = tmp.apply(pd.to_numeric, errors="coerce")
        corr = tmp.corr(numeric_only=True)

        if corr.shape[0] >= 2:
            fig = px.imshow(
                corr.round(2),
                aspect="auto",
                title="Correlation Heatmap (numeric columns)",
            )
            fig = style_fig(fig, height=520)
            st.plotly_chart(fig, use_container_width=True, key=pkey("pd_corr"))

            # Best quick drivers vs Net Sales
            if "Net Sales" in corr.columns:
                drivers = corr["Net Sales"].drop(labels=["Net Sales"]).dropna().sort_values(key=lambda s: s.abs(), ascending=False).head(8)
                ddf = drivers.reset_index()
                ddf.columns = ["Driver", "Correlation"]
                fig2 = px.bar(ddf, x="Correlation", y="Driver", orientation="h", title="Top Numeric Correlations vs Net Sales")
                fig2 = style_fig(fig2, height=380)
                st.plotly_chart(fig2, use_container_width=True, key=pkey("pd_corr_rank"))
        else:
            st.info("Not enough numeric columns to compute correlations.")

    # --- Data
    with p_tabs[4]:
        st.markdown("#### Raw Data – Price Drivers")
        cols = [
            "Sale ID", "Date", "Country", "Product Type", "Grade", "Finish",
            "Dominant Color", "Color Count (#)", "length", "width", "weight",
            "Area (mm²)", "Net Sales", "Price per mm²",
        ]
        cols = [c for c in cols if c in p_df.columns]
        subset = p_df[cols].copy()
        subset = subset.loc[:, ~subset.columns.duplicated()]
        st.dataframe(subset.head(max_rows), use_container_width=True)
        st.download_button(
            "Download price-driver subset (CSV)",
            data=subset.to_csv(index=False).encode("utf-8"),
            file_name="price_drivers_subset.csv",
            mime="text/csv",
            key="dl_price",
        )

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
            # 100% stacked
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

            # limit nodes for readability
            top_prod = m_df.groupby("Product Type")[metric_col].sum().sort_values(ascending=False).head(12).index
            sank = sank[sank["Product Type"].isin(top_prod)]

            labels = pd.Index(
                pd.concat([sank["Channel"], sank["Product Type"], sank["Grade"]]).unique()
            ).tolist()
            idx = {lab: i for i, lab in enumerate(labels)}

            # Channel -> Product Type
            a = sank.groupby(["Channel", "Product Type"], as_index=False)[metric_col].sum()
            # Product Type -> Grade
            b = sank.groupby(["Product Type", "Grade"], as_index=False)[metric_col].sum()

            src = [idx[x] for x in a["Channel"]] + [idx[x] for x in b["Product Type"]]
            tgt = [idx[x] for x in a["Product Type"]] + [idx[x] for x in b["Grade"]]
            val = a[metric_col].tolist() + b[metric_col].tolist()

            fig = go.Figure(data=[go.Sankey(
                node=dict(label=labels, pad=14, thickness=14),
                link=dict(source=src, target=tgt, value=val),
            )])
            fig.update_layout(title=f"Sankey – {metric_label}", height=520, margin=dict(l=10, r=10, t=60, b=10))
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
            .agg(Orders=("Sale ID", "count") if safe_col(s_df, "Sale ID") else ("OrderCount", "sum"),
                 Total_Net_Sales=("Net Sales", "sum"),
                 Avg_Order=("Net Sales", "mean"))
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
                title="Customer Value – Orders vs Total Net Sales (bubble = avg
