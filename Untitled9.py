import streamlit as st
import pathlib
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# Try optional Prophet for forecasting
try:
    from prophet import Prophet  # type: ignore
    HAS_PROPHET = True
except Exception:
    HAS_PROPHET = False

st.set_page_config(page_title="Dinosty 2025 • Unified Dashboard", layout="wide")

# ---------- DATA LOADING ----------

BASE_DIR = pathlib.Path(__file__).parent

CSV_CANDIDATES = [
    "Combined_Sales_2025.csv",
    "Combined_Sales_2025 (2).csv",
    "Combined_Sales_2025-2.csv",
]

@st.cache_data(show_spinner=True)
def load_data():
    data_file = None
    for name in CSV_CANDIDATES:
        p = BASE_DIR / name
        if p.exists():
            data_file = p
            break
    if data_file is None:
        st.error(
            "Dataset file not found. "
            "Place one of these in the same folder as this app: "
            + ", ".join(CSV_CANDIDATES)
        )
        st.stop()

    df = pd.read_csv(data_file)

    # Basic cleaning & derived fields
    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    if "Shipped Date" in df.columns:
        df["Shipped Date"] = pd.to_datetime(df["Shipped Date"], errors="coerce")

    # Ensure numeric
    for col in ["Price (CAD)", "Discount (CAD)", "Shipping (CAD)", "Taxes Collected (CAD)"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Fill important categoricals
    if "Channel" in df.columns:
        df["Channel"] = df["Channel"].fillna("Unknown")
    if "Country" in df.columns:
        df["Country"] = df["Country"].fillna("Unknown")
    if "City" in df.columns:
        df["City"] = df["City"].fillna("Unknown")
    if "Grade" in df.columns:
        df["Grade"] = df["Grade"].fillna("Unknown").astype(str)
    if "Customer Type" in df.columns:
        df["Customer Type"] = df["Customer Type"].fillna("Buyer (Jewelry)").replace("", "Buyer (Jewelry)")

    # Derived metrics
    if {"Price (CAD)", "Discount (CAD)"}.issubset(df.columns):
        df["Net Revenue"] = df["Price (CAD)"] - df["Discount (CAD)"]
    else:
        df["Net Revenue"] = np.nan

    if {"Net Revenue", "Shipping (CAD)", "Taxes Collected (CAD)"}.issubset(df.columns):
        df["Total Collected"] = (
            df["Net Revenue"]
            + df["Shipping (CAD)"].fillna(0)
            + df["Taxes Collected (CAD)"].fillna(0)
        )
    else:
        df["Total Collected"] = np.nan

    if {"Price (CAD)", "Discount (CAD)", "Shipping (CAD)", "Taxes Collected (CAD)"}.issubset(df.columns):
        df["True Spend"] = (
            df["Price (CAD)"]
            - df["Discount (CAD)"]
            + df["Shipping (CAD)"]
            + df["Taxes Collected (CAD)"]
        )
    else:
        df["True Spend"] = df.get("Net Revenue", np.nan)

    if {"Date", "Shipped Date"}.issubset(df.columns):
        df["Days_To_Ship"] = (df["Shipped Date"] - df["Date"]).dt.days

    if "Date" in df.columns:
        df["YearMonth"] = df["Date"].dt.to_period("M").astype(str)

    # Area for size drivers
    for dim in ["length", "width"]:
        if dim in df.columns:
            df[dim] = pd.to_numeric(df[dim], errors="coerce")
    if {"length", "width"}.issubset(df.columns):
        df["Area"] = df["length"] * df["width"]

    return df

df = load_data()

# ---------- GLOBAL SIDEBAR FILTERS ----------

st.sidebar.title("Dinosty 2025 Dashboard Filters")

if "Date" in df.columns and df["Date"].notna().any():
    min_date = df["Date"].min()
    max_date = df["Date"].max()
    date_range = st.sidebar.date_input(
        "Date range",
        [min_date, max_date],
        min_value=min_date,
        max_value=max_date,
    )
    if isinstance(date_range, (list, tuple)):
        start_date, end_date = date_range
    else:
        start_date = min_date
        end_date = max_date
else:
    start_date = None
    end_date = None

countries = sorted(df["Country"].dropna().unique()) if "Country" in df.columns else []
selected_countries = st.sidebar.multiselect(
    "Country",
    countries,
    default=countries if len(countries) <= 10 else countries[:10],
)

channels = sorted(df["Channel"].dropna().unique()) if "Channel" in df.columns else []
selected_channels = st.sidebar.multiselect(
    "Channel",
    channels,
    default=channels if len(channels) <= 6 else channels[:6],
)

cust_types = sorted(df["Customer Type"].dropna().unique()) if "Customer Type" in df.columns else []
selected_cust_types = st.sidebar.multiselect(
    "Customer Type",
    cust_types,
    default=[],
)

grades = sorted(df["Grade"].dropna().unique()) if "Grade" in df.columns else []
selected_grades = st.sidebar.multiselect(
    "Grade",
    grades,
    default=[],
)

filtered = df.copy()

if start_date is not None and end_date is not None and "Date" in filtered.columns:
    filtered = filtered[
        (filtered["Date"] >= pd.to_datetime(start_date))
        & (filtered["Date"] <= pd.to_datetime(end_date))
    ]

if selected_countries:
    filtered = filtered[filtered["Country"].isin(selected_countries)]
if selected_channels:
    filtered = filtered[filtered["Channel"].isin(selected_channels)]
if selected_cust_types:
    filtered = filtered[filtered["Customer Type"].isin(selected_cust_types)]
if selected_grades:
    filtered = filtered[filtered["Grade"].isin(selected_grades)]

if filtered.empty:
    st.error("No data matches the current filters. Try relaxing filters in the sidebar.")
    st.stop()

# ---------- MAIN LAYOUT ----------

st.title("Dinosty 2025 – Unified Sales Dashboard")

# High-level KPI row based on filtered data
total_revenue = filtered["True Spend"].sum() if "True Spend" in filtered.columns else np.nan
total_orders = filtered["Sale ID"].nunique() if "Sale ID" in filtered.columns else len(filtered)
avg_order_value = total_revenue / total_orders if total_orders else np.nan
unique_customers = filtered["Customer Type"].nunique() if "Customer Type" in filtered.columns else np.nan

kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.metric("Total Revenue (True Spend)", f"${total_revenue:,.0f}" if pd.notna(total_revenue) else "N/A")
kpi2.metric("Total Orders", f"{total_orders:,}")
kpi3.metric("Avg Order Value", f"${avg_order_value:,.0f}" if pd.notna(avg_order_value) else "N/A")
kpi4.metric("Customer Types", f"{int(unique_customers)}" if pd.notna(unique_customers) else "N/A")

# Tabs for main topics
tab1, tab2, tab3, tab4 = st.tabs(
    [
        "Customer Segmentation",
        "Geography & Channels",
        "Price Drivers & Correlations",
        "Overall Sales EDA",
    ]
)

# ---------- TAB 1: CUSTOMER SEGMENTATION ----------

with tab1:
    st.subheader("Customer Segmentation")

    # Revenue by Customer Type
    if {"Customer Type", "True Spend"}.issubset(filtered.columns):
        rev_by_cust = (
            filtered.groupby("Customer Type", dropna=False)["True Spend"]
            .sum()
            .reset_index()
            .sort_values("True Spend", ascending=False)
        )
        fig = px.bar(
            rev_by_cust,
            x="Customer Type",
            y="True Spend",
            title="Revenue by Customer Type",
            labels={"True Spend": "Revenue (CAD)"},
            text_auto=".2s",
            color="True Spend",
            color_continuous_scale="Blues",
        )
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Customer Type / True Spend columns not available.")

    # Monthly revenue trend
    if {"Date", "True Spend"}.issubset(filtered.columns):
        monthly = (
            filtered.dropna(subset=["Date"])
            .set_index("Date")
            .resample("M")["True Spend"]
            .sum()
            .reset_index()
        )
        if not monthly.empty:
            monthly["YearMonth"] = monthly["Date"].dt.to_period("M").astype(str)
            fig = px.line(
                monthly,
                x="YearMonth",
                y="True Spend",
                title="Monthly Revenue Trend",
                markers=True,
                labels={"YearMonth": "Month", "True Spend": "Revenue (CAD)"},
            )
            fig.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)

    # Treemap by Customer Type & Grade
    if {"Customer Type", "Grade", "True Spend"}.issubset(filtered.columns):
        seg = (
            filtered.groupby(["Customer Type", "Grade"], dropna=False)["True Spend"]
            .sum()
            .reset_index()
        )
        fig = px.treemap(
            seg,
            path=["Customer Type", "Grade"],
            values="True Spend",
            title="Revenue Distribution by Customer Type & Grade",
            color="True Spend",
            color_continuous_scale="Viridis",
        )
        st.plotly_chart(fig, use_container_width=True)

    # Pareto curve by customer type
    if {"Customer Type", "True Spend"}.issubset(filtered.columns):
        pareto = (
            filtered.groupby("Customer Type")["True Spend"]
            .sum()
            .sort_values(ascending=False)
            .reset_index()
        )
        total = pareto["True Spend"].sum()
        pareto["Revenue_Share"] = pareto["True Spend"] / total if total else 0
        pareto["Cumulative_Share"] = pareto["Revenue_Share"].cumsum()
        pareto["Rank"] = np.arange(1, len(pareto) + 1)
        pareto["Customer_Percentile"] = pareto["Rank"] / len(pareto)

        fig = px.line(
            pareto,
            x="Customer_Percentile",
            y="Cumulative_Share",
            title="Customer Revenue Concentration (Pareto Curve)",
            labels={
                "Customer_Percentile": "Customer Percentile",
                "Cumulative_Share": "Cumulative Revenue Share",
            },
        )
        fig.add_hline(y=0.8, line_dash="dash", line_color="red")
        fig.add_vline(x=0.2, line_dash="dash", line_color="red")
        st.plotly_chart(fig, use_container_width=True)

    # Optional: simple Prophet forecast
    if HAS_PROPHET and {"Date", "True Spend"}.issubset(filtered.columns):
        st.markdown("---")
        st.subheader("30-Day Revenue Forecast (Prophet)")
        ts = (
            filtered.dropna(subset=["Date"])
            .groupby("Date")["True Spend"]
            .sum()
            .reset_index()
        )
        ts = ts.rename(columns={"Date": "ds", "True Spend": "y"})
        if len(ts) > 10:
            try:
                model = Prophet(yearly_seasonality=True, weekly_seasonality=False, daily_seasonality=False)
                model.fit(ts)
                future = model.make_future_dataframe(periods=30)
                forecast = model.predict(future)

                fig = go.Figure()
                fig.add_trace(
                    go.Scatter(
                        x=ts["ds"],
                        y=ts["y"],
                        mode="lines",
                        name="Historical",
                    )
                )
                fig.add_trace(
                    go.Scatter(
                        x=forecast["ds"],
                        y=forecast["yhat"],
                        mode="lines",
                        name="Forecast",
                    )
                )
                fig.update_layout(
                    title="Total Revenue Forecast (Next 30 Days)",
                    xaxis_title="Date",
                    yaxis_title="Revenue (CAD)",
                )
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.info(f"Forecasting skipped due to error in Prophet: {e}")
        else:
            st.info("Not enough data points for forecasting.")
    elif not HAS_PROPHET:
        st.info("Prophet is not installed; skipping forecast section.")

    st.markdown("---")
    st.subheader("Filtered Data Preview")
    st.dataframe(filtered.head(200), use_container_width=True)

# ---------- TAB 2: GEOGRAPHY & CHANNELS ----------

with tab2:
    st.subheader("Geography & Channels")

    metric = st.selectbox(
        "Metric for geographic views",
        ["Net Revenue", "Total Collected", "True Spend", "Price (CAD)"],
        index=0,
    )

    if metric not in filtered.columns:
        st.warning(f"Selected metric '{metric}' not available in data.")
    else:
        # Choropleth by country
        if "Country" in filtered.columns:
            geo = (
                filtered.groupby("Country", dropna=False)[metric]
                .sum()
                .reset_index()
                .sort_values(metric, ascending=False)
            )
            fig = px.choropleth(
                geo,
                locations="Country",
                locationmode="country names",
                color=metric,
                hover_name="Country",
                projection="natural earth",
                title=f"{metric} by Country",
            )
            fig.update_layout(margin=dict(l=0, r=0, t=40, b=0))
            st.plotly_chart(fig, use_container_width=True)

        # Country × Channel heatmap
        if {"Country", "Channel"}.issubset(filtered.columns):
            pivot = filtered.pivot_table(
                index="Country",
                columns="Channel",
                values=metric,
                aggfunc="sum",
                fill_value=0,
            )
            fig = px.imshow(
                pivot,
                labels={"x": "Channel", "y": "Country", "color": metric},
                title=f"{metric} by Country × Channel",
                aspect="auto",
            )
            st.plotly_chart(fig, use_container_width=True)
            with st.expander("Show pivot table"):
                st.dataframe(pivot, use_container_width=True)

        # Time trend by country
        if {"Date", "Country"}.issubset(filtered.columns):
            ts_geo = (
                filtered.dropna(subset=["Date"])
                .groupby(["Date", "Country"])[metric]
                .sum()
                .reset_index()
            )
            ts_geo["YearMonth"] = ts_geo["Date"].dt.to_period("M").astype(str)
            fig = px.line(
                ts_geo,
                x="YearMonth",
                y=metric,
                color="Country",
                title=f"Monthly {metric} by Country",
                markers=True,
            )
            fig.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)

        # Shipping delay vs metric
        if {"Days_To_Ship", metric}.issubset(filtered.columns):
            lag_df = filtered.dropna(subset=["Days_To_Ship", metric])
            if not lag_df.empty:
                fig = px.scatter(
                    lag_df,
                    x="Days_To_Ship",
                    y=metric,
                    color="Country" if "Country" in lag_df.columns else None,
                    title=f"Shipping Delay vs {metric}",
                    labels={"Days_To_Ship": "Days to Ship"},
                    trendline="ols",
                )
                st.plotly_chart(fig, use_container_width=True)

# ---------- TAB 3: PRICE DRIVERS & CORRELATIONS ----------

with tab3:
    st.subheader("Price Drivers & Correlation Analysis")

    # Correlation heatmap
    numeric_candidates = [
        "Price (CAD)",
        "Net Revenue",
        "Total Collected",
        "True Spend",
        "Color Count (#)",
        "Discount (CAD)",
        "Shipping (CAD)",
        "Taxes Collected (CAD)",
        "length",
        "width",
        "Area",
        "weight",
        "Days_To_Ship",
    ]
    numeric_cols = [c for c in numeric_candidates if c in filtered.columns]

    if len(numeric_cols) >= 2:
        corr = filtered[numeric_cols].corr()
        fig = px.imshow(
            corr,
            text_auto=False,
            aspect="auto",
            title="Correlation Heatmap – Price & Operational Drivers",
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Not enough numeric columns to build a correlation matrix.")

    # Color Count vs Price
    if {"Color Count (#)", "Price (CAD)"}.issubset(filtered.columns):
        fig = px.scatter(
            filtered,
            x="Color Count (#)",
            y="Price (CAD)",
            color="Grade" if "Grade" in filtered.columns else None,
            title="Color Count vs Price",
            trendline="ols",
        )
        st.plotly_chart(fig, use_container_width=True)

    # Area vs Price
    if {"Area", "Price (CAD)"}.issubset(filtered.columns):
        fig = px.scatter(
            filtered,
            x="Area",
            y="Price (CAD)",
            color="Grade" if "Grade" in filtered.columns else None,
            title="Area vs Price",
            labels={"Area": "Area (length × width)"},
            trendline="ols",
        )
        st.plotly_chart(fig, use_container_width=True)

    # Price distribution
    if "Price (CAD)" in filtered.columns:
        fig = px.histogram(
            filtered,
            x="Price (CAD)",
            nbins=40,
            title="Price Distribution",
        )
        st.plotly_chart(fig, use_container_width=True)

    # Net Revenue / True Spend distribution
    if "True Spend" in filtered.columns:
        fig = px.histogram(
            filtered,
            x="True Spend",
            nbins=40,
            title="True Spend Distribution",
        )
        st.plotly_chart(fig, use_container_width=True)

# ---------- TAB 4: OVERALL SALES EDA ----------

with tab4:
    st.subheader("Overall Sales EDA")

    # Revenue by Product Type
    if {"Product Type", "Net Revenue"}.issubset(filtered.columns):
        rev_type = (
            filtered.groupby("Product Type")["Net Revenue"]
            .sum()
            .sort_values(ascending=False)
            .reset_index()
        )
        fig = px.bar(
            rev_type,
            x="Product Type",
            y="Net Revenue",
            title="Net Revenue by Product Type",
            labels={"Net Revenue": "Net Revenue (CAD)"},
            text_auto=".2s",
        )
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)

    # Product Type × Grade stacked bar
    if {"Product Type", "Grade", "Net Revenue"}.issubset(filtered.columns):
        cross = (
            filtered.groupby(["Product Type", "Grade"])["Net Revenue"]
            .sum()
            .reset_index()
        )
        fig = px.bar(
            cross,
            x="Product Type",
            y="Net Revenue",
            color="Grade",
            title="Net Revenue by Product Type & Grade",
        )
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)

    # Price by Product Type (boxplot)
    if {"Product Type", "Price (CAD)"}.issubset(filtered.columns):
        fig = px.box(
            filtered,
            x="Product Type",
            y="Price (CAD)",
            title="Price Distribution by Product Type",
        )
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)

    # Shipping time vs Net Revenue
    if {"Days_To_Ship", "Net Revenue"}.issubset(filtered.columns):
        ship = filtered.dropna(subset=["Days_To_Ship", "Net Revenue"])
        if not ship.empty:
            fig = px.scatter(
                ship,
                x="Days_To_Ship",
                y="Net Revenue",
                title="Shipping Time vs Net Revenue",
                labels={"Days_To_Ship": "Days to Ship", "Net Revenue": "Net Revenue (CAD)"},
                trendline="ols",
                color="Product Type" if "Product Type" in ship.columns else None,
            )
            st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.subheader("Sample of Filtered Dataset")
    st.dataframe(filtered.head(200), use_container_width=True)
