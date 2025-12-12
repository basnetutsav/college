# ==========================================================
# Global Ammolite Sales Dashboard – Full Streamlit App
# Expanded version with more charts per tab
# ==========================================================

import pandas as pd
import numpy as np
from pathlib import Path

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

# -----------------------------
# Page Config & Basic Styling
# -----------------------------
st.set_page_config(
    page_title="Global Ammolite Sales Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown(
    """
    <style>
    html, body, [class*="css"] {
        font-size: 1.0rem !important;
    }
    .block-container {
        padding-top: 1rem;
        padding-bottom: 2.2rem;
        max-width: 1500px;
    }
    [data-testid="metric-container"] {
        padding: 0.8rem 0.9rem !important;
    }
    [data-testid="stMetricValue"] {
        font-size: 1.5rem !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# -----------------------------
# Data Loading & Preparation
# -----------------------------
@st.cache_data
def load_data():
    possible_paths = [
        "Combined_Sales_2025.csv",
        "data/Combined_Sales_2025.csv",
        "/mnt/data/Combined_Sales_2025.csv",
    ]

    csv_path = None
    for p in possible_paths:
        if Path(p).exists():
            csv_path = p
            break

    if csv_path is None:
        st.error(
            "❌ CSV file not found.\n\n"
            "Place **Combined_Sales_2025.csv** in the same folder as this app."
        )
        st.stop()

    df = pd.read_csv(csv_path)

    # --- Basic cleaning ---
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].astype(str).str.strip()

    # Date handling
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df["Shipped Date"] = pd.to_datetime(df["Shipped Date"], errors="coerce")

    # Core metrics
    df["Net Sales"] = df["Price (CAD)"] - df["Discount (CAD)"]
    df["Shipping & Taxes"] = df["Shipping (CAD)"] + df["Taxes Collected (CAD)"]

    # Ownership
    df["Is Consigned"] = df["Consignment? (Y/N)"].str.upper().eq("Y")
    df["Ownership"] = np.where(df["Is Consigned"], "Consigned", "Owned")

    # Timing
    df["Days to Ship"] = (df["Shipped Date"] - df["Date"]).dt.days

    # Geometry
    if "length" in df.columns and "width" in df.columns:
        df["Area (mm²)"] = df["length"] * df["width"]
        df["Price per mm²"] = df["Net Sales"] / df["Area (mm²)"]
        df.loc[~np.isfinite(df["Price per mm²"]), "Price per mm²"] = np.nan
    else:
        df["Area (mm²)"] = np.nan
        df["Price per mm²"] = np.nan

    # Time dimensions
    df["Year"] = df["Date"].dt.year
    df["Month"] = df["Date"].dt.to_period("M").dt.to_timestamp()
    df["Month Name"] = df["Date"].dt.strftime("%b")
    df["Month Number"] = df["Date"].dt.month
    df["Quarter"] = df["Date"].dt.to_period("Q").astype(str)
    df["Day Name"] = df["Date"].dt.day_name()

    # Compliance fields
    df["Has Export Permit"] = (
        df["Export Permit (PDF link)"].astype(str).str.strip().ne("")
        & df["Export Permit (PDF link)"].notna()
    )
    df["Has COA"] = (
        df["COA #"].astype(str).str.strip().ne("")
        & df["COA #"].notna()
    )
    df["Is Export"] = df["Country"].ne("Canada")

    return df


df = load_data()

# -----------------------------
# Sidebar Filters
# -----------------------------
st.sidebar.title("Filters")

min_date = df["Date"].min()
max_date = df["Date"].max()

date_range = st.sidebar.date_input(
    "Sale Date Range",
    value=(min_date.date(), max_date.date()),
    min_value=min_date.date(),
    max_value=max_date.date(),
)

country_options = sorted(df["Country"].dropna().unique())
selected_countries = st.sidebar.multiselect(
    "Countries",
    options=country_options,
    default=[],
)

channel_options = sorted(df["Channel"].dropna().unique())
selected_channels = st.sidebar.multiselect(
    "Channels",
    options=channel_options,
    default=[],
)

cust_type_options = sorted(df["Customer Type"].dropna().unique())
selected_cust_types = st.sidebar.multiselect(
    "Customer Types",
    options=cust_type_options,
    default=[],
)


def apply_filters(data):
    if isinstance(date_range, tuple) and len(date_range) == 2:
        start, end = date_range
    else:
        start, end = min_date.date(), max_date.date()

    mask = pd.Series(True, index=data.index)

    # Date range
    mask &= data["Date"].between(pd.to_datetime(start), pd.to_datetime(end))

    # Country
    if selected_countries:
        mask &= data["Country"].isin(selected_countries)

    # Channel
    if selected_channels:
        mask &= data["Channel"].isin(selected_channels)

    # Customer type
    if selected_cust_types:
        mask &= data["Customer Type"].isin(selected_cust_types)

    return data[mask].copy()


filtered_df = apply_filters(df)

if filtered_df.empty:
    st.warning("No data after applying filters. Adjust filters in the sidebar.")
    st.stop()

# -----------------------------
# Helper: style Plotly figures
# -----------------------------
def style_fig(fig, height=420):
    fig.update_layout(
        height=height,
        margin=dict(l=10, r=10, t=50, b=40),
        xaxis=dict(title_font=dict(size=13), tickfont=dict(size=11)),
        yaxis=dict(title_font=dict(size=13), tickfont=dict(size=11)),
        legend=dict(font=dict(size=11)),
        hoverlabel=dict(font_size=11),
    )
    return fig


def bar_top_countries(data, metric="Net Sales", top_n=10):
    agg = (
        data.groupby("Country", as_index=False)[metric]
        .sum()
        .sort_values(metric, ascending=False)
        .head(top_n)
    )
    fig = px.bar(
        agg,
        x="Country",
        y=metric,
        title=f"Top {top_n} Countries by {metric}",
        text_auto=".2s",
    )
    fig.update_layout(xaxis_title="", yaxis_title="CAD", hovermode="x unified")
    return style_fig(fig)


def bar_channels(data, metric="Net Sales"):
    agg = (
        data.groupby("Channel", as_index=False)[metric]
        .sum()
        .sort_values(metric, ascending=False)
    )
    fig = px.bar(
        agg,
        x="Channel",
        y=metric,
        title=f"{metric} by Channel",
        text_auto=".2s",
    )
    fig.update_layout(xaxis_title="", yaxis_title="CAD", hovermode="x unified")
    return style_fig(fig)


# -----------------------------
# Top-Level Title & KPIs
# -----------------------------
st.title("Global Ammolite Sales Dashboard")

total_net_sales = filtered_df["Net Sales"].sum()
total_orders = len(filtered_df)
unique_customers = filtered_df["Customer Name"].nunique()
avg_order_value = total_net_sales / total_orders if total_orders > 0 else 0
consigned_share = filtered_df["Is Consigned"].mean() if total_orders > 0 else 0
avg_days_to_ship = filtered_df["Days to Ship"].mean()

kpi_cols = st.columns(5)
with kpi_cols[0]:
    st.metric("Total Net Sales (CAD)", f"${total_net_sales:,.0f}")
with kpi_cols[1]:
    st.metric("Total Orders", f"{total_orders:,}")
with kpi_cols[2]:
    st.metric("Unique Customers", f"{unique_customers:,}")
with kpi_cols[3]:
    st.metric("Avg Order Value", f"${avg_order_value:,.0f}")
with kpi_cols[4]:
    st.metric("Consigned Share", f"{consigned_share * 100:,.1f}%")

st.markdown("---")

# -----------------------------
# Tabs for Assignment Themes
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
    tab_plan,
) = st.tabs(
    [
        "Overview",
        "Price",
        "Product Mix",
        "Segments",
        "Geo & Channels",
        "Timing",
        "Ownership",
        "Seasonality",
        "Compliance",
        "Plan",
    ]
)

# -----------------------------
# TAB 1 – Overview
# -----------------------------
with tab_overview:
    st.subheader("Executive Overview")

    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(bar_top_countries(filtered_df), use_container_width=True)
    with c2:
        st.plotly_chart(bar_channels(filtered_df), use_container_width=True)

    # Product Type & Customer Segment snapshot
    prod_rev = (
        filtered_df.groupby("Product Type", as_index=False)["Net Sales"]
        .sum()
        .sort_values("Net Sales", ascending=False)
    )
    fig_prod = px.bar(
        prod_rev,
        x="Net Sales",
        y="Product Type",
        orientation="h",
        title="Net Sales by Product Type",
        text_auto=".2s",
    )
    fig_prod.update_layout(xaxis_title="Net Sales (CAD)", yaxis_title="")
    fig_prod = style_fig(fig_prod)

    seg_rev = (
        filtered_df.groupby("Customer Type", as_index=False)["Net Sales"]
        .sum()
        .sort_values("Net Sales", ascending=False)
    )
    fig_seg = px.bar(
        seg_rev,
        x="Net Sales",
        y="Customer Type",
        orientation="h",
        title="Net Sales by Customer Segment",
        text_auto=".2s",
    )
    fig_seg.update_layout(xaxis_title="Net Sales (CAD)", yaxis_title="")
    fig_seg = style_fig(fig_seg)

    c3, c4 = st.columns(2)
    with c3:
        st.plotly_chart(fig_prod, use_container_width=True)
    with c4:
        st.plotly_chart(fig_seg, use_container_width=True)

    # Top cities
    city_rev = (
        filtered_df.groupby("City", as_index=False)["Net Sales"]
        .sum()
        .sort_values("Net Sales", ascending=False)
        .head(10)
    )
    fig_city = px.bar(
        city_rev,
        x="City",
        y="Net Sales",
        title="Top 10 Cities by Net Sales",
        text_auto=".2s",
    )
    fig_city.update_layout(xaxis_title="", yaxis_title="Net Sales (CAD)")
    fig_city = style_fig(fig_city)

    st.plotly_chart(fig_city, use_container_width=True)

# -----------------------------
# TAB 2 – Price Drivers
# -----------------------------
with tab_price:
    st.subheader("Price Drivers – Grade, Colour, Size")

    grade_order = ["AAA", "AA", "A", "B", "Collectibles"]
    grade_order = [g for g in grade_order if g in filtered_df["Grade"].unique()]

    # Boxplot: Net Sales by Grade
    fig_box_grade = px.box(
        filtered_df,
        x="Grade",
        y="Net Sales",
        category_orders={"Grade": grade_order},
        title="Distribution of Net Sales by Grade",
        points="all",
    )
    fig_box_grade.update_layout(xaxis_title="Grade", yaxis_title="Net Sales (CAD)")
    fig_box_grade = style_fig(fig_box_grade)

    # Scatter: Colour Count vs Net Sales
    fig_color_scatter = px.scatter(
        filtered_df,
        x="Color Count (#)",
        y="Net Sales",
        color="Finish",
        size="weight",
        hover_data=["Grade", "Product Type", "Country"],
        title="Net Sales vs Colour Count (by Finish & Weight)",
    )
    fig_color_scatter.update_layout(
        xaxis_title="Colour Count (#)",
        yaxis_title="Net Sales (CAD)",
    )
    fig_color_scatter = style_fig(fig_color_scatter)

    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(fig_box_grade, use_container_width=True)
    with c2:
        st.plotly_chart(fig_color_scatter, use_container_width=True)

    # Heatmap: Grade x Finish – Average Net Sales
    price_grid = (
        filtered_df.pivot_table(
            index="Grade",
            columns="Finish",
            values="Net Sales",
            aggfunc="mean",
        )
        .fillna(0)
        .round(0)
    )
    if not price_grid.empty:
        fig_heat_price = px.imshow(
            price_grid,
            labels=dict(x="Finish", y="Grade", color="Avg Net Sales (CAD)"),
            title="Average Net Sales by Grade & Finish",
            aspect="auto",
        )
        fig_heat_price = style_fig(fig_heat_price)
        st.plotly_chart(fig_heat_price, use_container_width=True)

    # Boxplot: Price per mm² by Grade (if available)
    if filtered_df["Price per mm²"].notna().any():
        fig_ppm = px.box(
            filtered_df.dropna(subset=["Price per mm²"]),
            x="Grade",
            y="Price per mm²",
            category_orders={"Grade": grade_order},
            title="Price per mm² by Grade",
            points="all",
        )
        fig_ppm.update_layout(
            xaxis_title="Grade",
            yaxis_title="Price per mm² (CAD/mm²)",
        )
        fig_ppm = style_fig(fig_ppm)
        st.plotly_chart(fig_ppm, use_container_width=True)

    # Histogram: Net Sales by Weight
    if "weight" in filtered_df.columns:
        fig_weight = px.histogram(
            filtered_df,
            x="weight",
            color="Grade",
            nbins=30,
            title="Distribution of Weight by Grade",
        )
        fig_weight.update_layout(
            xaxis_title="Weight",
            yaxis_title="Count of Items",
        )
        fig_weight = style_fig(fig_weight)
        st.plotly_chart(fig_weight, use_container_width=True)

# -----------------------------
# TAB 3 – Product Mix
# -----------------------------
with tab_mix:
    st.subheader("Product Mix – Revenue & Volume")

    # Net Sales by Product Type
    prod_rev = (
        filtered_df.groupby("Product Type", as_index=False)["Net Sales"]
        .sum()
        .sort_values("Net Sales", ascending=False)
    )
    fig_prod_rev = px.bar(
        prod_rev,
        x="Product Type",
        y="Net Sales",
        title="Net Sales by Product Type",
        text_auto=".2s",
    )
    fig_prod_rev.update_layout(xaxis_title="", yaxis_title="Net Sales (CAD)")
    fig_prod_rev = style_fig(fig_prod_rev)

    # Order Count by Product Type
    prod_cnt = (
        filtered_df.groupby("Product Type", as_index=False)["Sale ID"]
        .count()
        .rename(columns={"Sale ID": "Order Count"})
        .sort_values("Order Count", ascending=False)
    )
    fig_prod_cnt = px.bar(
        prod_cnt,
        x="Product Type",
        y="Order Count",
        title="Order Count by Product Type",
        text_auto=True,
    )
    fig_prod_cnt.update_layout(xaxis_title="", yaxis_title="Orders")
    fig_prod_cnt = style_fig(fig_prod_cnt)

    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(fig_prod_rev, use_container_width=True)
    with c2:
        st.plotly_chart(fig_prod_cnt, use_container_width=True)

    # Average price per product type
    prod_avg = (
        filtered_df.groupby("Product Type", as_index=False)["Net Sales"]
        .mean()
        .sort_values("Net Sales", ascending=False)
    )
    fig_prod_avg = px.bar(
        prod_avg,
        x="Net Sales",
        y="Product Type",
        orientation="h",
        title="Average Net Sales per Order – by Product Type",
        text_auto=".0f",
    )
    fig_prod_avg.update_layout(xaxis_title="Avg Net Sales (CAD)", yaxis_title="")
    fig_prod_avg = style_fig(fig_prod_avg)

    # Treemap: Product Type -> Grade
    fig_treemap = px.treemap(
        filtered_df,
        path=["Product Type", "Grade"],
        values="Net Sales",
        title="Product Revenue Tree – Product Type & Grade",
    )
    fig_treemap = style_fig(fig_treemap, height=480)

    c3, c4 = st.columns(2)
    with c3:
        st.plotly_chart(fig_prod_avg, use_container_width=True)
    with c4:
        st.plotly_chart(fig_treemap, use_container_width=True)

    # Product Type × Channel stacked bar
    prod_channel = (
        filtered_df.groupby(["Product Type", "Channel"], as_index=False)["Net Sales"]
        .sum()
    )
    fig_prod_channel = px.bar(
        prod_channel,
        x="Product Type",
        y="Net Sales",
        color="Channel",
        barmode="stack",
        title="Net Sales by Product Type & Channel",
    )
    fig_prod_channel.update_layout(xaxis_title="", yaxis_title="Net Sales (CAD)")
    fig_prod_channel = style_fig(fig_prod_channel, height=450)

    st.plotly_chart(fig_prod_channel, use_container_width=True)

# -----------------------------
# TAB 4 – Customer Segments
# -----------------------------
with tab_segments:
    st.subheader("Customer Segments – Who Buys?")

    # Net Sales by Segment
    seg_rev = (
        filtered_df.groupby("Customer Type", as_index=False)["Net Sales"]
        .sum()
        .sort_values("Net Sales", ascending=False)
    )
    fig_seg_rev = px.bar(
        seg_rev,
        x="Customer Type",
        y="Net Sales",
        title="Net Sales by Customer Segment",
        text_auto=".2s",
    )
    fig_seg_rev.update_layout(xaxis_title="", yaxis_title="Net Sales (CAD)")
    fig_seg_rev = style_fig(fig_seg_rev)

    # Segment share pie chart
    fig_seg_pie = px.pie(
        seg_rev,
        names="Customer Type",
        values="Net Sales",
        title="Share of Net Sales by Customer Segment",
        hole=0.3,
    )
    fig_seg_pie = style_fig(fig_seg_pie, height=420)

    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(fig_seg_rev, use_container_width=True)
    with c2:
        st.plotly_chart(fig_seg_pie, use_container_width=True)

    # Customer Type x Channel
    seg_channel = (
        filtered_df.groupby(["Customer Type", "Channel"], as_index=False)["Net Sales"]
        .sum()
    )
    fig_seg_channel = px.bar(
        seg_channel,
        x="Customer Type",
        y="Net Sales",
        color="Channel",
        barmode="stack",
        title="Net Sales by Customer Segment & Channel",
    )
    fig_seg_channel.update_layout(xaxis_title="", yaxis_title="Net Sales (CAD)")
    fig_seg_channel = style_fig(fig_seg_channel, height=450)

    st.plotly_chart(fig_seg_channel, use_container_width=True)

    # Customer level stats
    customer_stats = (
        filtered_df.groupby(["Customer Name", "Customer Type"], as_index=False)
        .agg(
            Orders=("Sale ID", "count"),
            Total_Net_Sales=("Net Sales", "sum"),
        )
        .sort_values("Total_Net_Sales", ascending=False)
    )

    c3, c4 = st.columns([1.3, 1])
    with c3:
        st.markdown("**Top 15 Customers by Net Sales**")
        st.dataframe(
            customer_stats.head(15).style.format({"Total_Net_Sales": "{:,.0f}"}),
            use_container_width=True,
        )
    with c4:
        fig_cust_scatter = px.scatter(
            customer_stats,
            x="Orders",
            y="Total_Net_Sales",
            color="Customer Type",
            title="Customer Value – Orders vs Total Net Sales",
            hover_data=["Customer Name"],
        )
        fig_cust_scatter.update_layout(
            xaxis_title="Number of Orders",
            yaxis_title="Total Net Sales (CAD)",
        )
        fig_cust_scatter = style_fig(fig_cust_scatter, height=420)
        st.plotly_chart(fig_cust_scatter, use_container_width=True)

# -----------------------------
# TAB 5 – Geography & Channels
# -----------------------------
with tab_geo:
    st.subheader("Geography & Channels – Where and How We Sell")

    # World map – Net Sales by Country
    country_rev = (
        filtered_df.groupby("Country", as_index=False)["Net Sales"]
        .sum()
        .sort_values("Net Sales", ascending=False)
    )
    fig_map = px.choropleth(
        country_rev,
        locations="Country",
        locationmode="country names",
        color="Net Sales",
        title="Net Sales by Country (World Map)",
        hover_name="Country",
        color_continuous_scale="Viridis",
    )
    fig_map.update_layout(margin=dict(l=0, r=0, t=40, b=0))
    fig_map = style_fig(fig_map, height=450)

    st.plotly_chart(fig_map, use_container_width=True)

    # Heatmap: Country x Channel
    geo_channel = (
        filtered_df.pivot_table(
            index="Country",
            columns="Channel",
            values="Net Sales",
            aggfunc="sum",
        )
        .fillna(0)
        .round(0)
    )
    if not geo_channel.empty:
        fig_geo_channel = px.imshow(
            geo_channel,
            labels=dict(x="Channel", y="Country", color="Net Sales (CAD)"),
            title="Revenue Heatmap – Country × Channel",
            aspect="auto",
        )
        fig_geo_channel = style_fig(fig_geo_channel, height=520)
        st.plotly_chart(fig_geo_channel, use_container_width=True)

    # Top 10 countries by Channel mix (grouped bar)
    top_countries = country_rev.head(10)["Country"].tolist()
    cc = filtered_df[filtered_df["Country"].isin(top_countries)]
    country_channel = (
        cc.groupby(["Country", "Channel"], as_index=False)["Net Sales"]
        .sum()
    )
    fig_country_channel = px.bar(
        country_channel,
        x="Country",
        y="Net Sales",
        color="Channel",
        barmode="group",
        title="Top 10 Countries – Channel Mix",
    )
    fig_country_channel.update_layout(
        xaxis_title="Country",
        yaxis_title="Net Sales (CAD)",
    )
    fig_country_channel = style_fig(fig_country_channel, height=450)

    # Top 10 cities
    city_rev = (
        filtered_df.groupby(["Country", "City"], as_index=False)["Net Sales"]
        .sum()
        .sort_values("Net Sales", ascending=False)
        .head(10)
    )
    fig_city = px.bar(
        city_rev,
        x="Net Sales",
        y="City",
        color="Country",
        orientation="h",
        title="Top 10 City Markets",
        text_auto=".2s",
    )
    fig_city.update_layout(
        xaxis_title="Net Sales (CAD)",
        yaxis_title="City",
    )
    fig_city = style_fig(fig_city, height=450)

    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(fig_country_channel, use_container_width=True)
    with c2:
        st.plotly_chart(fig_city, use_container_width=True)

# -----------------------------
# TAB 6 – Inventory Timing
# -----------------------------
with tab_timing:
    st.subheader("Inventory Timing – Speed from Sale to Shipment")

    valid_timing = filtered_df.dropna(subset=["Days to Ship"])

    if valid_timing.empty:
        st.info("No valid shipping timing data available.")
    else:
        # Boxplot by Channel
        fig_box_ship = px.box(
            valid_timing,
            x="Channel",
            y="Days to Ship",
            title="Days to Ship by Channel",
            points="all",
        )
        fig_box_ship.update_layout(xaxis_title="Channel", yaxis_title="Days to Ship")
        fig_box_ship = style_fig(fig_box_ship)

        # Trend: average Days to Ship by Month
        monthly_ship = (
            valid_timing.groupby("Month", as_index=False)["Days to Ship"]
            .mean()
            .sort_values("Month")
        )
        fig_line_ship = px.line(
            monthly_ship,
            x="Month",
            y="Days to Ship",
            markers=True,
            title="Average Days to Ship – Monthly Trend",
        )
        fig_line_ship.update_layout(xaxis_title="Month", yaxis_title="Days to Ship")
        fig_line_ship = style_fig(fig_line_ship)

        c1, c2 = st.columns(2)
        with c1:
            st.plotly_chart(fig_box_ship, use_container_width=True)
        with c2:
            st.plotly_chart(fig_line_ship, use_container_width=True)

        # Histogram of Days to Ship
        fig_hist_ship = px.histogram(
            valid_timing,
            x="Days to Ship",
            nbins=30,
            title="Distribution of Days to Ship",
        )
        fig_hist_ship.update_layout(
            xaxis_title="Days to Ship",
            yaxis_title="Number of Orders",
        )
        fig_hist_ship = style_fig(fig_hist_ship)
        st.plotly_chart(fig_hist_ship, use_container_width=True)

        # Scatter: Days to Ship vs Net Sales
        fig_ship_sales = px.scatter(
            valid_timing,
            x="Days to Ship",
            y="Net Sales",
            color="Channel",
            title="Net Sales vs Days to Ship (by Channel)",
            hover_data=["Country", "Customer Name"],
        )
        fig_ship_sales.update_layout(
            xaxis_title="Days to Ship",
            yaxis_title="Net Sales (CAD)",
        )
        fig_ship_sales = style_fig(fig_ship_sales, height=440)
        st.plotly_chart(fig_ship_sales, use_container_width=True)

# -----------------------------
# TAB 7 – Ownership (Consigned vs Owned)
# -----------------------------
with tab_ownership:
    st.subheader("Ownership – Consigned vs Owned Inventory")

    # Revenue by Ownership
    ownership_rev = (
        filtered_df.groupby("Ownership", as_index=False)["Net Sales"]
        .sum()
        .sort_values("Net Sales", ascending=False)
    )
    fig_owner_rev = px.bar(
        ownership_rev,
        x="Ownership",
        y="Net Sales",
        title="Net Sales by Ownership Type",
        text_auto=".2s",
    )
    fig_owner_rev.update_layout(xaxis_title="", yaxis_title="Net Sales (CAD)")
    fig_owner_rev = style_fig(fig_owner_rev)

    # Item count by Ownership
    ownership_cnt = (
        filtered_df.groupby("Ownership", as_index=False)["Sale ID"]
        .count()
        .rename(columns={"Sale ID": "Order Count"})
    )
    fig_owner_cnt = px.pie(
        ownership_cnt,
        names="Ownership",
        values="Order Count",
        hole=0.3,
        title="Share of Orders – Consigned vs Owned",
    )
    fig_owner_cnt = style_fig(fig_owner_cnt, height=420)

    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(fig_owner_rev, use_container_width=True)
    with c2:
        st.plotly_chart(fig_owner_cnt, use_container_width=True)

    # Days to Ship by Ownership
    valid_own = filtered_df.dropna(subset=["Days to Ship"])
    if not valid_own.empty:
        fig_owner_ship = px.box(
            valid_own,
            x="Ownership",
            y="Days to Ship",
            title="Days to Ship by Ownership",
            points="all",
        )
        fig_owner_ship.update_layout(xaxis_title="", yaxis_title="Days to Ship")
        fig_owner_ship = style_fig(fig_owner_ship, height=430)
        st.plotly_chart(fig_owner_ship, use_container_width=True)

    # Ownership × Channel
    owner_channel = (
        filtered_df.groupby(["Ownership", "Channel"], as_index=False)["Net Sales"]
        .sum()
    )
    fig_owner_channel = px.bar(
        owner_channel,
        x="Channel",
        y="Net Sales",
        color="Ownership",
        barmode="group",
        title="Net Sales by Ownership & Channel",
    )
    fig_owner_channel.update_layout(
        xaxis_title="Channel",
        yaxis_title="Net Sales (CAD)",
    )
    fig_owner_channel = style_fig(fig_owner_channel, height=430)
    st.plotly_chart(fig_owner_channel, use_container_width=True)

# -----------------------------
# TAB 8 – Seasonality
# -----------------------------
with tab_seasonality:
    st.subheader("Seasonality – Time Patterns in Sales")

    # Monthly Net Sales
    monthly_rev = (
        filtered_df.groupby("Month", as_index=False)["Net Sales"]
        .sum()
        .sort_values("Month")
    )
    fig_monthly_rev = px.line(
        monthly_rev,
        x="Month",
        y="Net Sales",
        markers=True,
        title="Monthly Net Sales Trend",
    )
    fig_monthly_rev.update_layout(xaxis_title="Month", yaxis_title="Net Sales (CAD)")
    fig_monthly_rev = style_fig(fig_monthly_rev, height=430)
    st.plotly_chart(fig_monthly_rev, use_container_width=True)

    # Quarter-level view
    quarter_rev = (
        filtered_df.groupby("Quarter", as_index=False)["Net Sales"]
        .sum()
        .sort_values("Quarter")
    )
    fig_quarter = px.bar(
        quarter_rev,
        x="Quarter",
        y="Net Sales",
        title="Net Sales by Quarter",
        text_auto=".2s",
    )
    fig_quarter.update_layout(xaxis_title="Quarter", yaxis_title="Net Sales (CAD)")
    fig_quarter = style_fig(fig_quarter, height=430)

    # Month × Channel heatmap
    month_channel = (
        filtered_df.pivot_table(
            index="Month Name",
            columns="Channel",
            values="Net Sales",
            aggfunc="sum",
        )
        .fillna(0)
    )
    month_order = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                   "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    month_channel = month_channel.reindex(
        [m for m in month_order if m in month_channel.index]
    )

    if not month_channel.empty:
        fig_month_channel = px.imshow(
            month_channel,
            labels=dict(x="Channel", y="Month", color="Net Sales (CAD)"),
            title="Seasonality Heatmap – Month × Channel",
            aspect="auto",
        )
        fig_month_channel = style_fig(fig_month_channel, height=430)

    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(fig_quarter, use_container_width=True)
    with c2:
        if not month_channel.empty:
            st.plotly_chart(fig_month_channel, use_container_width=True)

    # Day of Week pattern
    dow_rev = (
        filtered_df.groupby("Day Name", as_index=False)["Net Sales"]
        .sum()
    )
    dow_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    dow_rev["Day Name"] = pd.Categorical(dow_rev["Day Name"], categories=dow_order, ordered=True)
    dow_rev = dow_rev.sort_values("Day Name")

    fig_dow = px.bar(
        dow_rev,
        x="Day Name",
        y="Net Sales",
        title="Net Sales by Day of Week",
        text_auto=".2s",
    )
    fig_dow.update_layout(xaxis_title="Day of Week", yaxis_title="Net Sales (CAD)")
    fig_dow = style_fig(fig_dow, height=430)
    st.plotly_chart(fig_dow, use_container_width=True)

# -----------------------------
# TAB 9 – Compliance (COA / Export)
# -----------------------------
with tab_compliance:
    st.subheader("Compliance – COA & Export Permits")

    # COA coverage overall
    coa_counts = (
        filtered_df.groupby("Has COA", as_index=False)["Sale ID"]
        .count()
        .rename(columns={"Sale ID": "Count"})
    )
    coa_counts["Status"] = coa_counts["Has COA"].map(
        {True: "Has COA", False: "Missing COA"}
    )
    fig_coa = px.pie(
        coa_counts,
        names="Status",
        values="Count",
        hole=0.3,
        title="COA Coverage – All Shipments",
    )
    fig_coa = style_fig(fig_coa, height=420)

    # Export shipments – permit status
    export_df = filtered_df[filtered_df["Is Export"]]

    if export_df.empty:
        st.info("No export shipments in the filtered data.")
        st.plotly_chart(fig_coa, use_container_width=True)
    else:
        permit_counts = (
            export_df.groupby("Has Export Permit", as_index=False)["Sale ID"]
            .count()
            .rename(columns={"Sale ID": "Count"})
        )
        permit_counts["Status"] = permit_counts["Has Export Permit"].map(
            {True: "Compliant (Has Permit)", False: "Missing Permit"}
        )

        fig_permit = px.bar(
            permit_counts,
            x="Status",
            y="Count",
            title="Export Shipments – Permit Status",
            text_auto=True,
        )
        fig_permit.update_layout(xaxis_title="", yaxis_title="Number of Shipments")
        fig_permit = style_fig(fig_permit, height=420)

        c1, c2 = st.columns(2)
        with c1:
            st.plotly_chart(fig_coa, use_container_width=True)
        with c2:
            st.plotly_chart(fig_permit, use_container_width=True)

        # Countries with missing permits
        missing = export_df[~export_df["Has Export Permit"]]
        if not missing.empty:
            missing_by_country = (
                missing.groupby("Country", as_index=False)["Sale ID"]
                .count()
                .rename(columns={"Sale ID": "Missing Permit Count"})
                .sort_values("Missing Permit Count", ascending=False)
            )
            st.markdown("### Countries with Missing Export Permits")
            st.dataframe(missing_by_country, use_container_width=True)

        # COA coverage by country (top 10)
        coa_country = (
            filtered_df.groupby("Country", as_index=False)["Has COA"]
            .mean()
            .rename(columns={"Has COA": "COA Rate"})
            .sort_values("COA Rate", ascending=False)
            .head(10)
        )
        fig_coa_country = px.bar(
            coa_country,
            x="Country",
            y="COA Rate",
            title="Top 10 Countries – COA Coverage Rate",
            text_auto=".0%",
        )
        fig_coa_country.update_layout(
            xaxis_title="Country",
            yaxis_title="COA Coverage Rate",
            yaxis_tickformat=".0%",
        )
        fig_coa_country = style_fig(fig_coa_country, height=430)
        st.plotly_chart(fig_coa_country, use_container_width=True)

# -----------------------------
# TAB 10 – Dashboard Plan (Proposal)
# -----------------------------
with tab_plan:
    st.subheader("Dashboard Visualization Plan")

    st.markdown(
        """
        This tab summarises the key visuals that should appear in the final business dashboard.

        **Overview**  
        • Top countries and channels by Net Sales  
        • Product type and customer segment snapshots  
        • Top city markets  

        **Price Drivers**  
        • Distribution of Net Sales by grade  
        • Relationship between colour count, finish, weight, and Net Sales  
        • Average pricing by grade and finish (including price per mm²)  

        **Product Mix**  
        • Net Sales, order volume, and average order value by product type  
        • Revenue tree (Product Type → Grade)  
        • Channel mix for each product type  

        **Customer Segments**  
        • Net Sales and share by customer segment  
        • Segment × channel performance  
        • Top customers and their order behaviour  

        **Geography & Channels**  
        • Net Sales world map  
        • Country × channel revenue heatmap  
        • Channel mix for top countries and top city markets  

        **Inventory Timing**  
        • Days to Ship by channel and ownership  
        • Monthly shipping speed trend  
        • Distribution of Days to Ship and impact on Net Sales  

        **Ownership**  
        • Net Sales and order share for consigned vs owned inventory  
        • Shipping performance by ownership  
        • Channel mix for ownership types  

        **Seasonality**  
        • Monthly and quarterly Net Sales trends  
        • Seasonality heatmap by month × channel  
        • Day-of-week demand patterns  

        **Compliance**  
        • COA coverage across all shipments  
        • Export permit status for export shipments  
        • Countries with missing documentation and COA coverage by country  

        You can take screenshots from each tab or export charts as images to build a one-page summary or presentation
        for your company or assignment.
        """
    )
