import pandas as pd
import numpy as np
from pathlib import Path
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from itertools import count

# Global counter to give unique keys to every chart
_plot_counter = count()

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
    html, body, [class*="css"] {
        font-size: 0.95rem !important;
    }
    .block-container {
        padding-top: 0.8rem;
        padding-bottom: 2.0rem;
        max-width: 1500px;
    }
    div[data-testid="column"] {
        padding-left: 0.40rem;
        padding-right: 0.40rem;
    }
    [data-testid="metric-container"] {
        padding: 0.75rem 0.9rem !important;
    }
    [data-testid="metric-container"] [data-testid="stMetricValue"] {
        font-size: 1.55rem !important;
        overflow: visible !important;
        text-overflow: clip !important;
        white-space: normal !important;
        line-height: 1.2 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------
# Helper: Deduplicate columns
# -----------------------------
def deduplicate_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Rename duplicate columns by adding suffixes: col, col_1, col_2, ...
    This avoids pyarrow ValueError: Duplicate column names found.
    """
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

# -----------------------------
# Data Loading & Preparation
# -----------------------------
@st.cache_data(show_spinner=False)
def load_data():
    possible_paths = [
        "Combined_Sales_2025.csv",
        "Combined_Sales_2025 (2).csv",
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

    # Ensure unique column names
    df = deduplicate_columns(df)

    # Clean strings
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].astype(str).str.strip()

    # Dates
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df["Shipped Date"] = pd.to_datetime(df["Shipped Date"], errors="coerce")

    # Core metrics
    df["Net Sales"] = df["Price (CAD)"] - df["Discount (CAD)"]
    df["Total Collected"] = (
        df["Price (CAD)"] - df["Discount (CAD)"]
        + df["Shipping (CAD)"]
        + df["Taxes Collected (CAD)"]
    )
    df["OrderCount"] = 1

    # Ownership
    df["Is Consigned"] = df["Consignment? (Y/N)"].str.upper().eq("Y")
    df["Ownership"] = np.where(df["Is Consigned"], "Consigned", "Owned")

    # Timing
    df["Days to Ship"] = (df["Shipped Date"] - df["Date"]).dt.days

    # Area / price density
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

    # Compliance
    df["Has Export Permit"] = (
        df["Export Permit (PDF link)"].astype(str).str.strip().ne("")
        & df["Export Permit (PDF link)"].notna()
    )
    df["Has COA"] = (
        df["COA #"].astype(str).str.strip().ne("") & df["COA #"].notna()
    )
    df["Is Export"] = df["Country"].ne("Canada")

    return df


df = load_data()

# -----------------------------
# Sidebar Filters & Metric
# -----------------------------
st.sidebar.title("Filters")

min_date = df["Date"].min()
max_date = df["Date"].max()

date_range = st.sidebar.date_input(
    "Sale Date range",
    value=(min_date.date(), max_date.date()),
    min_value=min_date.date(),
    max_value=max_date.date(),
)

country_options = sorted(df["Country"].dropna().unique())
sel_countries = st.sidebar.multiselect(
    "Countries",
    options=country_options,
    default=[],
)

channel_options = sorted(df["Channel"].dropna().unique())
sel_channels = st.sidebar.multiselect(
    "Channels",
    options=channel_options,
    default=[],
)

cust_options = sorted(df["Customer Type"].dropna().unique())
sel_cust = st.sidebar.multiselect(
    "Customer types",
    options=cust_options,
    default=[],
)

metric_map = {
    "Net Sales (CAD)": "Net Sales",
    "Total Collected (CAD)": "Total Collected",
    "Order Count": "OrderCount",
}
metric_label = st.sidebar.selectbox(
    "Main metric for charts",
    options=list(metric_map.keys()),
    index=0,
)
metric_col = metric_map[metric_label]


def apply_filters(data: pd.DataFrame) -> pd.DataFrame:
    if isinstance(date_range, tuple) and len(date_range) == 2:
        start, end = date_range
    else:
        start, end = min_date.date(), max_date.date()

    mask = pd.Series(True, index=data.index)
    mask &= data["Date"].between(pd.to_datetime(start), pd.to_datetime(end))

    if sel_countries:
        mask &= data["Country"].isin(sel_countries)
    if sel_channels:
        mask &= data["Channel"].isin(sel_channels)
    if sel_cust:
        mask &= data["Customer Type"].isin(sel_cust)

    return data[mask].copy()


f = apply_filters(df)

if f.empty:
    st.warning("No rows match the current filters. Try widening your filters on the left.")
    st.stop()

# -----------------------------
# Helper for consistent style
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

# -----------------------------
# Top Title & KPIs
# -----------------------------
st.title("💎 Global Ammolite Sales Dashboard – All Themes")

total_metric = f[metric_col].sum()
total_net_sales = f["Net Sales"].sum()
total_orders = len(f)
unique_customers = f["Customer Name"].nunique()
cons_share = f["Is Consigned"].mean() if total_orders else 0.0
avg_days_to_ship = f["Days to Ship"].mean()

k1, k2, k3, k4, k5 = st.columns(5)
with k1:
    if metric_col == "OrderCount":
        st.metric(metric_label, f"{int(total_metric):,}")
    else:
        st.metric(metric_label, f"${total_metric:,.0f}")
with k2:
    st.metric("Total Net Sales", f"${total_net_sales:,.0f}")
with k3:
    st.metric("Total Orders", f"{total_orders:,}")
with k4:
    st.metric("Unique Customers", f"{unique_customers:,}")
with k5:
    st.metric("Consigned Share", f"{cons_share*100:,.1f}%")

st.caption(
    "Use the filters on the left to focus by date, country, channel, or customer segment. "
    "The metric selector controls the main value used in most charts."
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
# TAB: Overview
# -----------------------------
with tab_overview:
    st.subheader("Executive Overview")

    # Top countries & channels
    by_country = (
        f.groupby("Country", as_index=False)[metric_col]
        .sum()
        .sort_values(metric_col, ascending=False)
    )
    by_channel = (
        f.groupby("Channel", as_index=False)[metric_col]
        .sum()
        .sort_values(metric_col, ascending=False)
    )

    c1, c2 = st.columns(2)
    with c1:
        top_n = st.slider("Top N countries", 3, 15, 10, key="ov_top_countries")
        fig1 = px.bar(
            by_country.head(top_n),
            x="Country",
            y=metric_col,
            title=f"Top {top_n} Countries by {metric_label}",
            text_auto=".2s",
        )
        fig1.update_layout(xaxis_title="", yaxis_title=metric_label)
        fig1 = style_fig(fig1)
        st.plotly_chart(fig1, use_container_width=True, key=f"plot_{next(_plot_counter)}")

    with c2:
        fig2 = px.bar(
            by_channel,
            x="Channel",
            y=metric_col,
            title=f"{metric_label} by Channel",
            text_auto=".2s",
        )
        fig2.update_layout(xaxis_title="", yaxis_title=metric_label)
        fig2 = style_fig(fig2)
        st.plotly_chart(fig2, use_container_width=True, key=f"plot_{next(_plot_counter)}")

    # Product & segment snapshot
    prod_rev = (
        f.groupby("Product Type", as_index=False)[metric_col]
        .sum()
        .sort_values(metric_col, ascending=False)
    )
    seg_rev = (
        f.groupby("Customer Type", as_index=False)[metric_col]
        .sum()
        .sort_values(metric_col, ascending=False)
    )

    c3, c4 = st.columns(2)
    with c3:
        fig3 = px.bar(
            prod_rev,
            x=metric_col,
            y="Product Type",
            orientation="h",
            title=f"{metric_label} by Product Type",
            text_auto=".2s",
        )
        fig3.update_layout(xaxis_title=metric_label, yaxis_title="")
        fig3 = style_fig(fig3)
        st.plotly_chart(fig3, use_container_width=True, key=f"plot_{next(_plot_counter)}")

    with c4:
        fig4 = px.bar(
            seg_rev,
            x=metric_col,
            y="Customer Type",
            orientation="h",
            title=f"{metric_label} by Customer Segment",
            text_auto=".2s",
        )
        fig4.update_layout(xaxis_title=metric_label, yaxis_title="")
        fig4 = style_fig(fig4)
        st.plotly_chart(fig4, use_container_width=True, key=f"plot_{next(_plot_counter)}")

    top_country = by_country["Country"].iloc[0] if not by_country.empty else "N/A"
    top_channel = by_channel["Channel"].iloc[0] if not by_channel.empty else "N/A"
    share_top = (
        float(by_country[metric_col].iloc[0] / by_country[metric_col].sum())
        if by_country[metric_col].sum() > 0
        else np.nan
    )

    st.markdown("### Key Takeaways")
    bullets = []
    if np.isfinite(share_top):
        bullets.append(
            f"- **{top_country}** is the top country, contributing about **{share_top*100:.1f}%** of {metric_label.lower()}."
        )
    bullets.append(f"- **{top_channel}** is the leading channel in this filtered view.")
    bullets.append(
        "- Product and customer mix show where the business is strongest and where new experiments can be run."
    )
    bullets.append(
        "- Use the other tabs to dig into pricing, mix, geography, timing, ownership, and compliance."
    )
    st.markdown("\n".join(bullets))

# -----------------------------
# TAB: Price Drivers
# -----------------------------
with tab_price:
    st.subheader("Price Drivers – Grade, Colour, Size")

    p_tabs = st.tabs(["Overview", "Distributions", "Heatmaps", "Colour & Size vs Price", "Data"])
    p_df = f.copy()

    with p_tabs[0]:
        st.markdown("#### Price Overview by Grade & Finish")
        grade_order = ["AAA", "AA", "A", "B", "Collectibles"]
        grade_order = [g for g in grade_order if g in p_df["Grade"].unique()]

        rev_by_grade = (
            p_df.groupby("Grade", as_index=False)["Net Sales"]
            .sum()
            .sort_values("Net Sales", ascending=False)
        )
        fig = px.bar(
            rev_by_grade,
            x="Grade",
            y="Net Sales",
            title="Net Sales by Grade",
            text_auto=".2s",
        )
        fig.update_layout(xaxis_title="Grade", yaxis_title="Net Sales (CAD)")
        fig = style_fig(fig)
        st.plotly_chart(fig, use_container_width=True, key=f"plot_{next(_plot_counter)}")

        avg_price_grade = (
            p_df.groupby("Grade", as_index=False)["Net Sales"]
            .mean()
            .sort_values("Net Sales", ascending=False)
        )
        fig2 = px.bar(
            avg_price_grade,
            x="Grade",
            y="Net Sales",
            title="Average Net Sales per Order by Grade",
            text_auto=".0f",
        )
        fig2.update_layout(xaxis_title="Grade", yaxis_title="Avg Net Sales (CAD)")
        fig2 = style_fig(fig2)
        st.plotly_chart(fig2, use_container_width=True, key=f"plot_{next(_plot_counter)}")

    with p_tabs[1]:
        st.markdown("#### Distributions by Grade & Price")
        grade_order = ["AAA", "AA", "A", "B", "Collectibles"]
        grade_order = [g for g in grade_order if g in p_df["Grade"].unique()]

        box = px.box(
            p_df,
            x="Grade",
            y="Net Sales",
            category_orders={"Grade": grade_order},
            title="Net Sales Distribution by Grade",
            points="all",
        )
        box.update_layout(xaxis_title="Grade", yaxis_title="Net Sales (CAD)")
        box = style_fig(box)
        st.plotly_chart(box, use_container_width=True, key=f"plot_{next(_plot_counter)}")

        hist = px.histogram(
            p_df,
            x="Net Sales",
            nbins=40,
            color="Grade",
            title="Histogram of Net Sales (coloured by Grade)",
        )
        hist.update_layout(xaxis_title="Net Sales (CAD)", yaxis_title="Order Count")
        hist = style_fig(hist)
        st.plotly_chart(hist, use_container_width=True, key=f"plot_{next(_plot_counter)}")

    with p_tabs[2]:
        st.markdown("#### Heatmaps for Grade × Colour Count")

        # --- Heatmap 1: Avg Net Sales by Grade × Colour Count ---
        if "Color Count (#)" in p_df.columns:
            price_grid = (
                p_df.pivot_table(
                    index="Grade",
                    columns="Color Count (#)",
                    values="Net Sales",
                    aggfunc="mean",
                )
                .round(0)
            )

            if not price_grid.empty:
                hm = px.imshow(
                    price_grid,
                    labels=dict(
                        x="Colour Count (#)",
                        y="Grade",
                        color="Avg Net Sales (CAD)",
                    ),
                    title="Average Net Sales by Grade × Colour Count",
                    aspect="auto",
                )
                hm = style_fig(hm, height=450)
                st.plotly_chart(
                    hm,
                    use_container_width=True,
                    key=f"plot_{next(_plot_counter)}",
                )
            else:
                st.info("No data available for Grade × Colour Count heatmap.")
        else:
            st.info("No 'Color Count (#)' field available for heatmap.")

        # --- Heatmap 2: Price Density (CAD/mm²) by Grade × Colour Count ---
        if "Color Count (#)" in p_df.columns and p_df["Price per mm²"].notna().any():
            ppm_grid = (
                p_df.dropna(subset=["Price per mm²"])
                .pivot_table(
                    index="Grade",
                    columns="Color Count (#)",
                    values="Price per mm²",
                    aggfunc="mean",
                )
                .round(2)
            )

            if not ppm_grid.empty:
                hm2 = px.imshow(
                    ppm_grid,
                    labels=dict(
                        x="Colour Count (#)",
                        y="Grade",
                        color="Avg Price per mm²",
                    ),
                    title="Price Density by Grade × Colour Count (CAD/mm²)",
                    aspect="auto",
                )
                hm2 = style_fig(hm2, height=450)
                st.plotly_chart(
                    hm2,
                    use_container_width=True,
                    key=f"plot_{next(_plot_counter)}",
                )

    with p_tabs[3]:
        st.markdown("#### Colour & Size vs Price (Alternative Views)")

        # ---- Colour Count vs Price (bar) ----
        if "Color Count (#)" in p_df.columns:
            cc_stats = (
                p_df.groupby("Color Count (#)", as_index=False)["Net Sales"]
                .mean()
                .sort_values("Color Count (#)")
            )
            fig_cs1 = px.bar(
                cc_stats,
                x="Color Count (#)",
                y="Net Sales",
                title="Average Net Sales by Colour Count",
                text_auto=".0f",
            )
            fig_cs1.update_layout(
                xaxis_title="Colour Count (#)",
                yaxis_title="Avg Net Sales (CAD)",
            )
            fig_cs1 = style_fig(fig_cs1, height=430)
            st.plotly_chart(
                fig_cs1,
                use_container_width=True,
                key=f"plot_{next(_plot_counter)}",
            )
        else:
            st.info("No 'Color Count (#)' field available for this view.")

        # ---- Size vs Price (size buckets) ----
        if "Area (mm²)" in p_df.columns and p_df["Area (mm²)"].notna().sum() > 1:
            valid = p_df["Area (mm²)"].dropna()
            bins = np.linspace(valid.min(), valid.max(), 5)
            if len(np.unique(bins)) > 1:
                p_df.loc[valid.index, "Size Bucket"] = pd.cut(
                    valid, bins=bins, include_lowest=True
                )
                size_stats = (
                    p_df.dropna(subset=["Size Bucket"])
                    .groupby("Size Bucket", as_index=False)["Net Sales"]
                    .mean()
                )
                size_stats = size_stats.sort_values("Size Bucket")
                fig_cs2 = px.bar(
                    size_stats,
                    x="Size Bucket",
                    y="Net Sales",
                    title="Average Net Sales by Size Bucket (Area)",
                    text_auto=".0f",
                )
                fig_cs2.update_layout(
                    xaxis_title="Size Bucket (by Area)",
                    yaxis_title="Avg Net Sales (CAD)",
                )
                fig_cs2 = style_fig(fig_cs2, height=430)
                st.plotly_chart(
                    fig_cs2,
                    use_container_width=True,
                    key=f"plot_{next(_plot_counter)}",
                )
            else:
                st.info("Area values do not vary enough to form size buckets.")
        else:
            st.info("No valid area data to build size buckets.")

    with p_tabs[4]:
        st.markdown("#### Raw Data – Price Drivers")
        cols = [
            "Sale ID",
            "Date",
            "Country",
            "Product Type",
            "Grade",
            "Finish",
            "Color Count (#)",
            "length",
            "width",
            "weight",
            "Net Sales",
            "Price per mm²",
        ]
        cols = [c for c in cols if c in p_df.columns]
        subset = p_df[cols].copy()
        subset = subset.loc[:, ~subset.columns.duplicated()]
        st.dataframe(subset.head(300), use_container_width=True)
        st.download_button(
            "Download price-driver subset (CSV)",
            data=subset.to_csv(index=False).encode("utf-8"),
            file_name="price_drivers_subset.csv",
            mime="text/csv",
        )

# -----------------------------
# TAB: Product Mix
# -----------------------------
with tab_mix:
    st.subheader("Product Mix – Revenue & Volume")

    m_tabs = st.tabs(["Overview", "Channel Mix", "Grades", "Data"])
    m_df = f.copy()

    with m_tabs[0]:
        by_prod = (
            m_df.groupby("Product Type", as_index=False)[metric_col]
            .sum()
            .sort_values(metric_col, ascending=False)
        )
        fig1 = px.bar(
            by_prod,
            x="Product Type",
            y=metric_col,
            title=f"{metric_label} by Product Type",
            text_auto=".2s",
        )
        fig1.update_layout(xaxis_title="", yaxis_title=metric_label)
        fig1 = style_fig(fig1)
        st.plotly_chart(fig1, use_container_width=True, key=f"plot_{next(_plot_counter)}")

        avg_by_prod = (
            m_df.groupby("Product Type", as_index=False)["Net Sales"]
            .mean()
            .sort_values("Net Sales", ascending=False)
        )
        fig2 = px.bar(
            avg_by_prod,
            x="Net Sales",
            y="Product Type",
            orientation="h",
            title="Average Net Sales per Order – by Product Type",
            text_auto=".0f",
        )
        fig2.update_layout(xaxis_title="Avg Net Sales (CAD)", yaxis_title="")
        fig2 = style_fig(fig2)
        st.plotly_chart(fig2, use_container_width=True, key=f"plot_{next(_plot_counter)}")

    with m_tabs[1]:
        prod_channel = (
            m_df.groupby(["Product Type", "Channel"], as_index=False)[metric_col]
            .sum()
        )
        fig3 = px.bar(
            prod_channel,
            x="Product Type",
            y=metric_col,
            color="Channel",
            barmode="stack",
            title=f"{metric_label} by Product Type × Channel",
        )
        fig3.update_layout(xaxis_title="", yaxis_title=metric_label)
        fig3 = style_fig(fig3, height=460)
        st.plotly_chart(fig3, use_container_width=True, key=f"plot_{next(_plot_counter)}")

    with m_tabs[2]:
        fig4 = px.treemap(
            m_df,
            path=["Product Type", "Grade"],
            values=metric_col,
            title=f"{metric_label} Tree – Product Type → Grade",
        )
        fig4 = style_fig(fig4, height=480)
        st.plotly_chart(fig4, use_container_width=True, key=f"plot_{next(_plot_counter)}")

    with m_tabs[3]:
        cols = [
            "Sale ID",
            "Date",
            "Product Type",
            "Grade",
            "Channel",
            "Country",
            metric_col,
            "Net Sales",
        ]
        cols = [c for c in cols if c in m_df.columns]
        subset = m_df[cols].copy()
        subset = subset.loc[:, ~subset.columns.duplicated()]
        st.dataframe(subset.head(300), use_container_width=True)
        st.download_button(
            "Download product-mix subset (CSV)",
            data=subset.to_csv(index=False).encode("utf-8"),
            file_name="product_mix_subset.csv",
            mime="text/csv",
        )

# -----------------------------
# TAB: Customer Segments
# -----------------------------
with tab_segments:
    st.subheader("Customer Segments – Who Buys?")

    s_tabs = st.tabs(["Overview", "Segment × Channel", "Customer Value", "Data"])
    s_df = f.copy()

    with s_tabs[0]:
        seg_rev = (
            s_df.groupby("Customer Type", as_index=False)[metric_col]
            .sum()
            .sort_values(metric_col, ascending=False)
        )
        fig1 = px.bar(
            seg_rev,
            x="Customer Type",
            y=metric_col,
            title=f"{metric_label} by Customer Segment",
            text_auto=".2s",
        )
        fig1.update_layout(xaxis_title="", yaxis_title=metric_label)
        fig1 = style_fig(fig1)
        st.plotly_chart(fig1, use_container_width=True, key=f"plot_{next(_plot_counter)}")

        fig2 = px.pie(
            seg_rev,
            names="Customer Type",
            values=metric_col,
            title=f"Share of {metric_label} by Customer Segment",
            hole=0.3,
        )
        fig2 = style_fig(fig2, height=430)
        st.plotly_chart(fig2, use_container_width=True, key=f"plot_{next(_plot_counter)}")

    with s_tabs[1]:
        seg_channel = (
            s_df.groupby(["Customer Type", "Channel"], as_index=False)[metric_col]
            .sum()
        )
        fig3 = px.bar(
            seg_channel,
            x="Customer Type",
            y=metric_col,
            color="Channel",
            barmode="stack",
            title=f"{metric_label} by Segment × Channel",
        )
        fig3.update_layout(xaxis_title="", yaxis_title=metric_label)
        fig3 = style_fig(fig3, height=460)
        st.plotly_chart(fig3, use_container_width=True, key=f"plot_{next(_plot_counter)}")

    with s_tabs[2]:
        cust_stats = (
            s_df.groupby(["Customer Name", "Customer Type"], as_index=False)
            .agg(
                Orders=("Sale ID", "count"),
                Total_Net_Sales=("Net Sales", "sum"),
            )
            .sort_values("Total_Net_Sales", ascending=False)
        )
        c1, c2 = st.columns([1.3, 1])
        with c1:
            st.markdown("#### Top 15 Customers by Net Sales")
            st.dataframe(
                cust_stats.head(15).style.format({"Total_Net_Sales": "{:,.0f}"}),
                use_container_width=True,
            )
        with c2:
            fig4 = px.scatter(
                cust_stats,
                x="Orders",
                y="Total_Net_Sales",
                color="Customer Type",
                title="Customer Value – Orders vs Total Net Sales",
                hover_data=["Customer Name"],
            )
            fig4.update_layout(
                xaxis_title="Number of Orders",
                yaxis_title="Total Net Sales (CAD)",
            )
            fig4 = style_fig(fig4, height=430)
            st.plotly_chart(fig4, use_container_width=True, key=f"plot_{next(_plot_counter)}")

    with s_tabs[3]:
        cols = [
            "Sale ID",
            "Date",
            "Customer Name",
            "Customer Type",
            "Country",
            "City",
            "Channel",
            metric_col,
            "Net Sales",
        ]
        cols = [c for c in cols if c in s_df.columns]
        subset = s_df[cols].copy()
        subset = subset.loc[:, ~subset.columns.duplicated()]
        st.dataframe(subset.head(300), use_container_width=True)
        st.download_button(
            "Download customer-segment subset (CSV)",
            data=subset.to_csv(index=False).encode("utf-8"),
            file_name="customer_segments_subset.csv",
            mime="text/csv",
        )

# -----------------------------
# TAB: Geography & Channels
# -----------------------------
with tab_geo:
    st.subheader("Geography & Channels")

    g_tabs = st.tabs(["Overview", "World Map", "Country × Channel", "Top Markets", "Data"])
    g_df = f.copy()

    with g_tabs[0]:
        st.markdown("#### Key Geography Highlights")
        by_c = (
            g_df.groupby("Country", as_index=False)[metric_col]
            .sum()
            .sort_values(metric_col, ascending=False)
        )
        by_ch = (
            g_df.groupby("Channel", as_index=False)[metric_col]
            .sum()
            .sort_values(metric_col, ascending=False)
        )

        c1, c2 = st.columns(2)
        with c1:
            fig1 = px.bar(
                by_c.head(10),
                x="Country",
                y=metric_col,
                title=f"Top 10 Countries by {metric_label}",
                text_auto=".2s",
            )
            fig1.update_layout(xaxis_title="", yaxis_title=metric_label)
            fig1 = style_fig(fig1)
            st.plotly_chart(fig1, use_container_width=True, key=f"plot_{next(_plot_counter)}")
        with c2:
            fig2 = px.bar(
                by_ch,
                x="Channel",
                y=metric_col,
                title=f"{metric_label} by Channel",
                text_auto=".2s",
            )
            fig2.update_layout(xaxis_title="", yaxis_title=metric_label)
            fig2 = style_fig(fig2)
            st.plotly_chart(fig2, use_container_width=True, key=f"plot_{next(_plot_counter)}")

    with g_tabs[1]:
        st.markdown("#### World Map")
        country_totals = (
            g_df.groupby("Country", as_index=False)[metric_col]
            .sum()
            .sort_values(metric_col, ascending=False)
        )
        if not country_totals.empty:
            fig = px.choropleth(
                country_totals,
                locations="Country",
                locationmode="country names",
                color=metric_col,
                title=f"{metric_label} by Country (World Map)",
                hover_name="Country",
                color_continuous_scale="Viridis",
            )
            fig.update_layout(margin=dict(l=0, r=0, t=40, b=0))
            fig = style_fig(fig, height=480)
            st.plotly_chart(fig, use_container_width=True, key=f"plot_{next(_plot_counter)}")
        else:
            st.info("No country data available for current filters.")

    with g_tabs[2]:
        st.markdown("#### Country × Channel Heatmap")
        top_n = st.slider("Top N countries for heatmap", 3, 20, 10, key="geo_heat_top")
        country_totals = (
            g_df.groupby("Country")[metric_col]
            .sum()
            .sort_values(ascending=False)
        )
        top_idx = country_totals.head(top_n).index
        df_top = g_df[g_df["Country"].isin(top_idx)]
        pv = (
            df_top.pivot_table(
                values=metric_col,
                index="Country",
                columns="Channel",
                aggfunc="sum",
                fill_value=0,
            )
            .round(0)
        )
        if not pv.empty:
            hm = px.imshow(
                pv,
                labels=dict(x="Channel", y="Country", color=metric_label),
                title=f"{metric_label} Heatmap – Country × Channel",
                aspect="auto",
            )
            hm = style_fig(hm, height=480)
            st.plotly_chart(hm, use_container_width=True, key=f"plot_{next(_plot_counter)}")
        else:
            st.info("Heatmap is empty for current settings.")

    with g_tabs[3]:
        st.markdown("#### Top Markets & Cities")
        city_rev = (
            g_df.groupby(["Country", "City"], as_index=False)[metric_col]
            .sum()
            .sort_values(metric_col, ascending=False)
            .head(15)
        )
        fig1 = px.bar(
            city_rev,
            x=metric_col,
            y="City",
            color="Country",
            orientation="h",
            title=f"Top 15 City Markets by {metric_label}",
            text_auto=".2s",
        )
        fig1.update_layout(xaxis_title=metric_label, yaxis_title="City")
        fig1 = style_fig(fig1, height=480)
        st.plotly_chart(fig1, use_container_width=True, key=f"plot_{next(_plot_counter)}")

    with g_tabs[4]:
        cols = [
            "Sale ID",
            "Date",
            "Country",
            "City",
            "Channel",
            "Customer Type",
            metric_col,
            "Net Sales",
        ]
        cols = [c for c in cols if c in g_df.columns]
        subset = g_df[cols].copy()
        subset = subset.loc[:, ~subset.columns.duplicated()]
        st.dataframe(subset.head(300), use_container_width=True)
        st.download_button(
            "Download geography subset (CSV)",
            data=subset.to_csv(index=False).encode("utf-8"),
            file_name="geography_channels_subset.csv",
            mime="text/csv",
        )

# -----------------------------
# TAB: Inventory Timing
# -----------------------------
with tab_timing:
    st.subheader("Inventory Timing – Speed from Sale to Shipment")

    t_tabs = st.tabs(["Overview", "Distribution", "By Channel", "Trend", "Data"])
    t_df = f.dropna(subset=["Days to Ship"]).copy()

    if t_df.empty:
        st.info("No valid Days to Ship data for the current filters.")
    else:
        with t_tabs[0]:
            avg_lag = t_df["Days to Ship"].mean()
            p95 = t_df["Days to Ship"].quantile(0.95)
            st.markdown(
                f"""
                **Average Days to Ship:** `{avg_lag:.1f}`  
                **95th Percentile (long tail):** `{p95:.1f}` days  
                """
            )

        with t_tabs[1]:
            hist = px.histogram(
                t_df,
                x="Days to Ship",
                nbins=30,
                title="Distribution of Days to Ship",
            )
            hist.update_layout(
                xaxis_title="Days to Ship",
                yaxis_title="Number of Orders",
            )
            hist = style_fig(hist, height=430)
            st.plotly_chart(hist, use_container_width=True, key=f"plot_{next(_plot_counter)}")

        with t_tabs[2]:
            st.markdown("#### Days to Ship by Channel")

            # Average days to ship by channel
            avg_channel = (
                t_df.groupby("Channel", as_index=False)["Days to Ship"]
                .mean()
                .sort_values("Days to Ship")
            )
            fig = px.bar(
                avg_channel,
                x="Channel",
                y="Days to Ship",
                title="Average Days to Ship by Channel",
                text_auto=".1f",
            )
            fig.update_layout(xaxis_title="Channel", yaxis_title="Avg Days to Ship")
            fig = style_fig(fig, height=430)
            st.plotly_chart(
                fig,
                use_container_width=True,
                key=f"plot_{next(_plot_counter)}",
            )

            # Order volume by channel (context)
            vol_channel = (
                t_df.groupby("Channel", as_index=False)["Sale ID"]
                .count()
                .rename(columns={"Sale ID": "Order Count"})
                .sort_values("Order Count", ascending=False)
            )
            fig2 = px.bar(
                vol_channel,
                x="Channel",
                y="Order Count",
                title="Order Volume by Channel (Shipping Timing Context)",
                text_auto=True,
            )
            fig2.update_layout(xaxis_title="Channel", yaxis_title="Order Count")
            fig2 = style_fig(fig2, height=430)
            st.plotly_chart(
                fig2,
                use_container_width=True,
                key=f"plot_{next(_plot_counter)}",
            )

        with t_tabs[3]:
            monthly_ship = (
                t_df.groupby("Month", as_index=False)["Days to Ship"]
                .mean()
                .sort_values("Month")
            )
            fig = px.line(
                monthly_ship,
                x="Month",
                y="Days to Ship",
                markers=True,
                title="Average Days to Ship – Monthly Trend",
            )
            fig.update_layout(xaxis_title="Month", yaxis_title="Days to Ship")
            fig = style_fig(fig, height=430)
            st.plotly_chart(fig, use_container_width=True, key=f"plot_{next(_plot_counter)}")

        with t_tabs[4]:
            cols = [
                "Sale ID",
                "Date",
                "Country",
                "Channel",
                "Ownership",
                "Days to Ship",
                "Net Sales",
            ]
            cols = [c for c in cols if c in t_df.columns]
            subset = t_df[cols].copy()
            subset = subset.loc[:, ~subset.columns.duplicated()]
            st.dataframe(subset.head(300), use_container_width=True)
            st.download_button(
                "Download timing subset (CSV)",
                data=subset.to_csv(index=False).encode("utf-8"),
                file_name="inventory_timing_subset.csv",
                mime="text/csv",
            )

# -----------------------------
# TAB: Ownership
# -----------------------------
with tab_ownership:
    st.subheader("Ownership – Consigned vs Owned")

    o_tabs = st.tabs(["Overview", "Timing", "Channel Mix", "Data"])
    o_df = f.copy()

    with o_tabs[0]:
        own_rev = (
            o_df.groupby("Ownership", as_index=False)[metric_col]
            .sum()
            .sort_values(metric_col, ascending=False)
        )
        fig1 = px.bar(
            own_rev,
            x="Ownership",
            y=metric_col,
            title=f"{metric_label} by Ownership Type",
            text_auto=".2s",
        )
        fig1.update_layout(xaxis_title="", yaxis_title=metric_label)
        fig1 = style_fig(fig1)
        st.plotly_chart(fig1, use_container_width=True, key=f"plot_{next(_plot_counter)}")

        own_cnt = (
            o_df.groupby("Ownership", as_index=False)["Sale ID"]
            .count()
            .rename(columns={"Sale ID": "Order Count"})
        )
        fig2 = px.pie(
            own_cnt,
            names="Ownership",
            values="Order Count",
            title="Share of Orders – Consigned vs Owned",
            hole=0.35,
        )
        fig2 = style_fig(fig2, height=430)
        st.plotly_chart(fig2, use_container_width=True, key=f"plot_{next(_plot_counter)}")

    with o_tabs[1]:
        t_df2 = o_df.dropna(subset=["Days to Ship"]).copy()
        if t_df2.empty:
            st.info("No valid Days to Ship data.")
        else:
            fig3 = px.box(
                t_df2,
                x="Ownership",
                y="Days to Ship",
                title="Days to Ship by Ownership",
                points="all",
            )
            fig3.update_layout(xaxis_title="", yaxis_title="Days to Ship")
            fig3 = style_fig(fig3, height=430)
            st.plotly_chart(fig3, use_container_width=True, key=f"plot_{next(_plot_counter)}")

    with o_tabs[2]:
        own_channel = (
            o_df.groupby(["Ownership", "Channel"], as_index=False)[metric_col]
            .sum()
        )
        fig4 = px.bar(
            own_channel,
            x="Channel",
            y=metric_col,
            color="Ownership",
            barmode="group",
            title=f"{metric_label} by Ownership × Channel",
        )
        fig4.update_layout(xaxis_title="Channel", yaxis_title=metric_label)
        fig4 = style_fig(fig4, height=430)
        st.plotly_chart(fig4, use_container_width=True, key=f"plot_{next(_plot_counter)}")

    with o_tabs[3]:
        cols = [
            "Sale ID",
            "Date",
            "Country",
            "Channel",
            "Ownership",
            metric_col,
            "Net Sales",
        ]
        cols = [c for c in cols if c in o_df.columns]
        subset = o_df[cols].copy()
        subset = subset.loc[:, ~subset.columns.duplicated()]
        st.dataframe(subset.head(300), use_container_width=True)
        st.download_button(
            "Download ownership subset (CSV)",
            data=subset.to_csv(index=False).encode("utf-8"),
            file_name="ownership_subset.csv",
            mime="text/csv",
        )

# -----------------------------
# TAB: Seasonality
# -----------------------------
with tab_seasonality:
    st.subheader("Seasonality – Time Patterns in Sales")

    se_tabs = st.tabs(["Monthly & Quarterly", "Month × Channel", "Day-of-week", "Data"])
    se_df = f.copy()

    with se_tabs[0]:
        monthly_rev = (
            se_df.groupby("Month", as_index=False)[metric_col]
            .sum()
            .sort_values("Month")
        )
        fig1 = px.line(
            monthly_rev,
            x="Month",
            y=metric_col,
            markers=True,
            title=f"Monthly {metric_label}",
        )
        fig1.update_layout(xaxis_title="Month", yaxis_title=metric_label)
        fig1 = style_fig(fig1, height=430)
        st.plotly_chart(fig1, use_container_width=True, key=f"plot_{next(_plot_counter)}")

        quarter_rev = (
            se_df.groupby("Quarter", as_index=False)[metric_col]
            .sum()
            .sort_values("Quarter")
        )
        fig2 = px.bar(
            quarter_rev,
            x="Quarter",
            y=metric_col,
            title=f"{metric_label} by Quarter",
            text_auto=".2s",
        )
        fig2.update_layout(xaxis_title="Quarter", yaxis_title=metric_label)
        fig2 = style_fig(fig2, height=430)
        st.plotly_chart(fig2, use_container_width=True, key=f"plot_{next(_plot_counter)}")

    with se_tabs[1]:
        month_channel = (
            se_df.pivot_table(
                index="Month Name",
                columns="Channel",
                values=metric_col,
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
            hm = px.imshow(
                month_channel,
                labels=dict(x="Channel", y="Month", color=metric_label),
                title=f"Seasonality Heatmap – Month × Channel ({metric_label})",
                aspect="auto",
            )
            hm = style_fig(hm, height=460)
            st.plotly_chart(hm, use_container_width=True, key=f"plot_{next(_plot_counter)}")
        else:
            st.info("No data to display for Month × Channel.")

    with se_tabs[2]:
        dow_rev = (
            se_df.groupby("Day Name", as_index=False)[metric_col]
            .sum()
        )
        dow_order = [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday",
        ]
        dow_rev["Day Name"] = pd.Categorical(
            dow_rev["Day Name"], categories=dow_order, ordered=True
        )
        dow_rev = dow_rev.sort_values("Day Name")
        fig3 = px.bar(
            dow_rev,
            x="Day Name",
            y=metric_col,
            title=f"{metric_label} by Day of Week",
            text_auto=".2s",
        )
        fig3.update_layout(xaxis_title="Day of Week", yaxis_title=metric_label)
        fig3 = style_fig(fig3, height=430)
        st.plotly_chart(fig3, use_container_width=True, key=f"plot_{next(_plot_counter)}")

    with se_tabs[3]:
        cols = [
            "Sale ID",
            "Date",
            "Country",
            "Channel",
            "Month",
            "Quarter",
            "Day Name",
            metric_col,
            "Net Sales",
        ]
        cols = [c for c in cols if c in se_df.columns]
        subset = se_df[cols].copy()
        subset = subset.loc[:, ~subset.columns.duplicated()]
        st.dataframe(subset.head(300), use_container_width=True)
        st.download_button(
            "Download seasonality subset (CSV)",
            data=subset.to_csv(index=False).encode("utf-8"),
            file_name="seasonality_subset.csv",
            mime="text/csv",
        )

# -----------------------------
# TAB: Compliance
# -----------------------------
with tab_compliance:
    st.subheader("Compliance – COA & Export Permits")

    c_tabs = st.tabs(["COA Coverage", "Export Permits", "Country Risk", "Data"])
    c_df = f.copy()

    with c_tabs[0]:
        coa_counts = (
            c_df.groupby("Has COA", as_index=False)["Sale ID"]
            .count()
            .rename(columns={"Sale ID": "Count"})
        )
        coa_counts["Status"] = coa_counts["Has COA"].map(
            {True: "Has COA", False: "Missing COA"}
        )
        fig1 = px.pie(
            coa_counts,
            names="Status",
            values="Count",
            title="COA Coverage – All Shipments",
            hole=0.35,
        )
        fig1 = style_fig(fig1, height=430)
        st.plotly_chart(fig1, use_container_width=True, key=f"plot_{next(_plot_counter)}")

        coa_country = (
            c_df.groupby("Country", as_index=False)["Has COA"]
            .mean()
            .rename(columns={"Has COA": "COA Rate"})
            .sort_values("COA Rate", ascending=False)
            .head(10)
        )
        fig2 = px.bar(
            coa_country,
            x="Country",
            y="COA Rate",
            title="Top 10 Countries – COA Coverage Rate",
            text_auto=".0%",
        )
        fig2.update_layout(
            xaxis_title="Country",
            yaxis_title="COA Coverage Rate",
            yaxis_tickformat=".0%",
        )
        fig2 = style_fig(fig2, height=430)
        st.plotly_chart(fig2, use_container_width=True, key=f"plot_{next(_plot_counter)}")

    with c_tabs[1]:
        export_df = c_df[c_df["Is Export"]].copy()
        if export_df.empty:
            st.info("No export shipments in the current filters.")
        else:
            permit_counts = (
                export_df.groupby("Has Export Permit", as_index=False)["Sale ID"]
                .count()
                .rename(columns={"Sale ID": "Count"})
            )
            permit_counts["Status"] = permit_counts["Has Export Permit"].map(
                {True: "Compliant (Has Permit)", False: "Missing Permit"}
            )
            fig3 = px.bar(
                permit_counts,
                x="Status",
                y="Count",
                title="Export Shipments – Permit Status",
                text_auto=True,
            )
            fig3.update_layout(xaxis_title="", yaxis_title="Number of Shipments")
            fig3 = style_fig(fig3, height=430)
            st.plotly_chart(fig3, use_container_width=True, key=f"plot_{next(_plot_counter)}")

    with c_tabs[2]:
        export_df = c_df[c_df["Is Export"]].copy()
        if export_df.empty:
            st.info("No export shipments in the current filters.")
        else:
            missing = export_df[~export_df["Has Export Permit"]]
            if not missing.empty:
                missing_by_country = (
                    missing.groupby("Country", as_index=False)["Sale ID"]
                    .count()
                    .rename(columns={"Sale ID": "Missing Permit Count"})
                    .sort_values("Missing Permit Count", ascending=False)
                )
                st.markdown("#### Countries with Missing Export Permits")
                st.dataframe(missing_by_country, use_container_width=True)
            else:
                st.success("All export shipments have permits recorded in this view.")

    with c_tabs[3]:
        cols = [
            "Sale ID",
            "Date",
            "Country",
            "Channel",
            "Is Export",
            "Has COA",
            "Has Export Permit",
            metric_col,
            "Net Sales",
        ]
        cols = [c for c in cols if c in c_df.columns]
        subset = c_df[cols].copy()
        subset = subset.loc[:, ~subset.columns.duplicated()]
        st.dataframe(subset.head(300), use_container_width=True)
        st.download_button(
            "Download compliance subset (CSV)",
            data=subset.to_csv(index=False).encode("utf-8"),
            file_name="compliance_subset.csv",
            mime="text/csv",
        )

# -----------------------------
# TAB: All Data
# -----------------------------
with tab_data:
    st.subheader("All Filtered Data")

    st.markdown(
        "Full dataset after applying filters. "
        "Download for extra analysis if you need."
    )

    subset = f.copy()
    subset = subset.loc[:, ~subset.columns.duplicated()]
    st.dataframe(subset.head(500), use_container_width=True)
    st.download_button(
        "Download filtered dataset (CSV)",
        data=subset.to_csv(index=False).encode("utf-8"),
        file_name="ammolite_filtered_full.csv",
        mime="text/csv",
    )
