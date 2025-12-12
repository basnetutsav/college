# ==========================================================
# Global Ammolite Sales Dashboard – Full Streamlit App
# Covers: Price Drivers, Product Mix, Segments, Geography,
# Inventory Timing, Ownership, Seasonality, Compliance
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
    .block-container {
        padding-top: 1rem;
        padding-bottom: 2rem;
        max-width: 1500px;
    }
    .metric-small > div {
        padding: 0.6rem 0.8rem !important;
    }
    .metric-small [data-testid="stMetricValue"] {
        font-size: 1.4rem !important;
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
        "/mnt/data/Combined_Sales_2025.csv",  # for cloud / lab envs
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
    # Strip whitespace from object columns
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
    df["Area (mm²)"] = df["length"] * df["width"]
    df["Price per mm²"] = df["Net Sales"] / df["Area (mm²)"]
    df.loc[~np.isfinite(df["Price per mm²"]), "Price per mm²"] = np.nan

    # Time dimensions
    df["Year"] = df["Date"].dt.year
    df["Month"] = df["Date"].dt.to_period("M").dt.to_timestamp()
    df["Month Name"] = df["Date"].dt.strftime("%b")
    df["Month Number"] = df["Date"].dt.month
    df["Quarter"] = df["Date"].dt.to_period("Q").astype(str)

    # Compliance
    df["Has Export Permit"] = df["Export Permit (PDF link)"].astype(str).str.strip().ne("") & df["Export Permit (PDF link)"].notna()
    df["Is Export"] = df["Country"].ne("Canada")

    return df


df = load_data()

# -----------------------------
# Sidebar Filters
# -----------------------------
st.sidebar.title("🔍 Global Filters")

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
    help="Leave empty to include all countries.",
)

channel_options = sorted(df["Channel"].dropna().unique())
selected_channels = st.sidebar.multiselect(
    "Channels",
    options=channel_options,
    default=[],
    help="Leave empty to include all channels.",
)

cust_type_options = sorted(df["Customer Type"].dropna().unique())
selected_cust_types = st.sidebar.multiselect(
    "Customer Types",
    options=cust_type_options,
    default=[],
    help="Leave empty to include all customer types.",
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
    st.warning("No data after applying filters. Please adjust filters in the sidebar.")
    st.stop()

# -----------------------------
# Top-Level Title
# -----------------------------
st.title("💎 Global Ammolite Sales Dashboard")
st.caption(
    "Interactive analytics across price drivers, product mix, customers, geography, "
    "inventory timing, ownership, seasonality, and compliance."
)

# -----------------------------
# High-Level KPIs (based on filters)
# -----------------------------
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
# Helper Functions for Charts
# -----------------------------
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
    return fig


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
    return fig


# -----------------------------
# Tabs for Assignment Themes
# -----------------------------
(
    tab_overview,
    tab_price,
    tab_mix,
    tab_segments,
    tab_geo,
    tab_inventory,
    tab_ownership,
    tab_seasonality,
    tab_compliance,
    tab_plan,
) = st.tabs(
    [
        "📊 Overview",
        "💰 Price Drivers",
        "📦 Product Mix",
        "👥 Customer Segments",
        "🗺️ Geography & Channels",
        "⏱️ Inventory Timing",
        "🏷️ Ownership (Consigned vs Owned)",
        "📆 Seasonality",
        "✅ Compliance (COA / Export)",
        "📝 Dashboard Plan (Proposal)",
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

    st.markdown("### Product & Channel Snapshot")

    # Revenue by Product Type
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

    # Net Sales by Customer Type
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

    c3, c4 = st.columns(2)
    with c3:
        st.plotly_chart(fig_prod, use_container_width=True)
    with c4:
        st.plotly_chart(fig_seg, use_container_width=True)

    st.markdown(
        """
        **Quick Insight:**  
        • Top countries and channels drive a large share of revenue.  
        • Product mix and customer segments show where the brand is strongest and where new opportunities exist.
        """
    )

# -----------------------------
# TAB 2 – Price Drivers
# -----------------------------
with tab_price:
    st.subheader("Price Drivers – Grade, Colour & Size")

    # Boxplot: Net Sales by Grade
    grade_order = ["AAA", "AA", "A", "B", "Collectibles"]
    grade_order = [g for g in grade_order if g in filtered_df["Grade"].unique()]

    fig_box_grade = px.box(
        filtered_df,
        x="Grade",
        y="Net Sales",
        category_orders={"Grade": grade_order},
        title="Distribution of Net Sales by Grade",
        points="all",
    )
    fig_box_grade.update_layout(xaxis_title="Grade", yaxis_title="Net Sales (CAD)")

    # Scatter: Color Count vs Net Sales, coloured by Finish
    fig_color_scatter = px.scatter(
        filtered_df,
        x="Color Count (#)",
        y="Net Sales",
        color="Finish",
        size="weight",
        hover_data=["Grade", "Product Type", "Country"],
        title="Price vs Colour Count & Finish",
    )
    fig_color_scatter.update_layout(
        xaxis_title="Colour Count (#)",
        yaxis_title="Net Sales (CAD)",
    )

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
        st.plotly_chart(fig_heat_price, use_container_width=True)

    st.markdown(
        """
        **Hypothesis:**  
        Higher grade pieces and richer finishes (with more colour play) command higher prices.  

        **Key Insight:**  
        • Boxplots show a clear price uplift for premium grades (AAA/AA).  
        • Scatter suggests items with higher colour count and certain finishes tend to sell at higher prices.  
        • Heatmap highlights which grade–finish combinations deserve priority inventory and marketing focus.
        """
    )

# -----------------------------
# TAB 3 – Product Mix
# -----------------------------
with tab_mix:
    st.subheader("Product Mix – Revenue by Product Type & Grade")

    # Revenue by Product Type
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

    # Treemap: Product Type -> Grade
    fig_treemap = px.treemap(
        filtered_df,
        path=["Product Type", "Grade"],
        values="Net Sales",
        title="Product Revenue Tree – Product Type & Grade",
    )

    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(fig_prod_rev, use_container_width=True)
    with c2:
        st.plotly_chart(fig_treemap, use_container_width=True)

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

    st.plotly_chart(fig_prod_avg, use_container_width=True)

    st.markdown(
        """
        **Key Insight:**  
        • A small number of product categories typically drive most revenue.  
        • Treemap reveals which grades dominate within each product type and where premium pricing is being captured.
        """
    )

# -----------------------------
# TAB 4 – Customer Segments
# -----------------------------
with tab_segments:
    st.subheader("Customer Segments – Who Buys Ammolite?")

    # Revenue by Customer Type
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

    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(fig_seg_rev, use_container_width=True)
    with c2:
        st.plotly_chart(fig_seg_channel, use_container_width=True)

    # Top 10 customers table
    top_customers = (
        filtered_df.groupby(["Customer Name", "Customer Type"], as_index=False)[
            "Net Sales"
        ]
        .sum()
        .sort_values("Net Sales", ascending=False)
        .head(10)
    )
    st.markdown("### Top 10 Customers by Net Sales")
    st.dataframe(top_customers.style.format({"Net Sales": "{:,.0f}"}), use_container_width=True)

    st.markdown(
        """
        **Key Insight:**  
        • Certain segments (e.g., galleries, wholesalers, or retail collectors) contribute a disproportionate share of revenue.  
        • Combining segment + channel shows where to focus sales outreach and relationship management.
        """
    )

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
        st.plotly_chart(fig_geo_channel, use_container_width=True)

    st.markdown(
        """
        **Hypothesis:**  
        Certain countries and channels dominate sales and should anchor marketing, trade shows, and partnerships.  

        **Key Insight:**  
        • Map highlights core markets vs. emerging ones.  
        • Heatmap reveals which channels work best in each country (e.g., Online vs Gallery vs Wholesale).
        """
    )

# -----------------------------
# TAB 6 – Inventory Timing
# -----------------------------
with tab_inventory:
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

        c1, c2 = st.columns(2)
        with c1:
            st.plotly_chart(fig_box_ship, use_container_width=True)
        with c2:
            st.plotly_chart(fig_line_ship, use_container_width=True)

        st.markdown(
            """
            **Key Insight:**  
            • Certain channels show longer shipping times, which may impact customer satisfaction.  
            • Monitoring this monthly trend helps spot operational issues early (e.g., logistics bottlenecks).
            """
        )

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
        title="Net Sales by Ownership (Consigned vs Owned)",
        text_auto=".2s",
    )
    fig_owner_rev.update_layout(xaxis_title="", yaxis_title="Net Sales (CAD)")

    # Days to Ship by Ownership
    valid_own = filtered_df.dropna(subset=["Days to Ship"])
    fig_owner_ship = px.box(
        valid_own,
        x="Ownership",
        y="Days to Ship",
        title="Days to Ship by Ownership",
        points="all",
    )
    fig_owner_ship.update_layout(xaxis_title="", yaxis_title="Days to Ship")

    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(fig_owner_rev, use_container_width=True)
    with c2:
        st.plotly_chart(fig_owner_ship, use_container_width=True)

    st.markdown(
        """
        **Key Insight:**  
        • Compares revenue contribution of consigned vs owned pieces.  
        • Shipping speed differences can reveal whether consigned items move slower or faster than owned inventory.
        """
    )

# -----------------------------
# TAB 8 – Seasonality
# -----------------------------
with tab_seasonality:
    st.subheader("Seasonality – How Sales Move Over Time")

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

    st.plotly_chart(fig_monthly_rev, use_container_width=True)

    # Month vs Channel Heatmap
    month_channel = (
        filtered_df.pivot_table(
            index="Month Name",
            columns="Channel",
            values="Net Sales",
            aggfunc="sum",
        )
        .fillna(0)
    )
    # Reorder months in calendar order if present
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
        st.plotly_chart(fig_month_channel, use_container_width=True)

    st.markdown(
        """
        **Key Insight:**  
        • Line chart shows high/low sales periods (seasonality).  
        • Month × Channel heatmap reveals which channels perform best in peak seasons and where to push marketing.
        """
    )

# -----------------------------
# TAB 9 – Compliance (COA / Export)
# -----------------------------
with tab_compliance:
    st.subheader("Compliance – COA & Export Permits")

    st.markdown(
        "Focus on export shipments (non-Canada) and whether they have export permits recorded."
    )

    export_df = filtered_df[filtered_df["Is Export"]]

    if export_df.empty:
        st.info("No export shipments in the filtered data.")
    else:
        # Export compliance rate
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
            st.dataframe(
                missing_by_country,
                use_container_width=True,
            )
        else:
            st.success("All export shipments in the filtered data have permits recorded.")

    st.markdown(
        """
        **Key Insight:**  
        • Quick view of export compliance rate.  
        • Helps identify countries or partners where documentation is missing and follow-up is required.
        """
    )

# -----------------------------
# TAB 10 – Dashboard Plan (Proposal)
# -----------------------------
with tab_plan:
    st.subheader("Dashboard Visualization Proposal – Summary")

    st.markdown(
        """
        Below is a structured proposal for the visuals that should appear in the **final company dashboard**,
        organized by analytical theme from your assignment.

        ### 1. Price Drivers
        - **Metric:** Net Sales by Grade / Finish / Colour Count  
        - **Why it matters:** Shows which quality tiers and colour characteristics justify higher pricing; guides pricing strategy and grading standards.  
        - **Visuals Used:**  
          - Boxplot – Net Sales by Grade  
          - Scatter – Colour Count vs Net Sales (Finish as colour, weight as size)  
          - Heatmap – Avg Net Sales by Grade × Finish  

        ### 2. Product Mix
        - **Metric:** Net Sales & Average Order Value by Product Type & Grade  
        - **Why it matters:** Identifies hero products and underperformers; informs assortment planning and purchasing.  
        - **Visuals Used:**  
          - Bar – Net Sales by Product Type  
          - Treemap – Product Type → Grade (revenue tree)  
          - Bar – Average Net Sales per Order by Product Type  

        ### 3. Customer Segments
        - **Metric:** Net Sales by Customer Type & Channel; Top Customers  
        - **Why it matters:** Highlights most valuable customer segments and preferred channels; guides relationship management and trade incentives.  
        - **Visuals Used:**  
          - Bar – Net Sales by Customer Segment  
          - Stacked Bar – Segment × Channel  
          - Table – Top 10 Customers by Net Sales  

        ### 4. Geography & Channels
        - **Metric:** Net Sales by Country & Channel  
        - **Why it matters:** Shows global footprint and which channels work best in each region; supports market expansion decisions.  
        - **Visuals Used:**  
          - World Map – Net Sales by Country  
          - Heatmap – Country × Channel (Net Sales)  

        ### 5. Inventory Timing
        - **Metric:** Days to Ship by Channel & over Time  
        - **Why it matters:** Indicates operational efficiency and customer experience risk. Slow channels / months may signal bottlenecks.  
        - **Visuals Used:**  
          - Boxplot – Days to Ship by Channel  
          - Line – Average Days to Ship (Monthly Trend)  

        ### 6. Ownership (Consigned vs Owned)
        - **Metric:** Net Sales & Days to Ship by Ownership Type  
        - **Why it matters:** Shows financial contribution and velocity of consigned vs owned inventory, key for risk and cash flow.  
        - **Visuals Used:**  
          - Bar – Net Sales by Ownership  
          - Boxplot – Days to Ship by Ownership  

        ### 7. Seasonality
        - **Metric:** Monthly Net Sales & Month × Channel Revenue  
        - **Why it matters:** Identifies peak seasons and best-performing channels in each period; useful for event planning and ad spend.  
        - **Visuals Used:**  
          - Line – Monthly Net Sales Trend  
          - Heatmap – Month × Channel  

        ### 8. Compliance (COA / Export)
        - **Metric:** Export Shipments with vs without Permits; Missing Permits by Country  
        - **Why it matters:** Ensures regulatory compliance and reduces risk of shipment issues or fines.  
        - **Visuals Used:**  
          - Bar – Export Shipments by Permit Status  
          - Table – Countries with Missing Export Permits  

        ---

        This structure gives you a **complete, professional dashboard** that satisfies all assignment tasks:
        - Task 1: Exploratory questions + visuals + insights for each theme  
        - Task 2: Clear dashboard visualization proposal (this tab)  
        - Task 3: Easy for team leads to grab screenshots and build a one-page visual summary for Slack
        """
    )
