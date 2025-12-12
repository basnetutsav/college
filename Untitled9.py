import streamlit as st
import pathlib

st.set_page_config(page_title="Dinosty 2025 • Full Analytics Suite", layout="wide")

BASE_DIR = pathlib.Path(__file__).parent

# Try to find one of several possible dataset filenames
CSV_CANDIDATES = [
    "Combined_Sales_2025.csv",
    "Combined_Sales_2025 (2).csv",
    "Combined_Sales_2025-2.csv",
]
DATA_FILE = None
for name in CSV_CANDIDATES:
    p = BASE_DIR / name
    if p.exists():
        DATA_FILE = p
        break

if DATA_FILE is None:
    st.error(
        "Dataset file not found. Put one of these in the same folder as this app: "
        + ", ".join(CSV_CANDIDATES)
    )
    st.stop()

st.sidebar.title("Dinosty 2025 Analytics Suite")
page = st.sidebar.radio(
    "Select a dashboard",
    [
        "Customer Segmentation",
        "Geography & Channels",
        "Price Drivers & Correlations",
        "Overall Sales EDA",
    ],
)

if page == "Customer Segmentation":
    import pandas as pd
    import plotly.graph_objects as go
    import streamlit as st
    import plotly.express as px
    from prophet import Prophet
    from sklearn.linear_model import LinearRegression
    from sklearn.preprocessing import StandardScaler

    st.markdown(
        """
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css"> 
        <style>
        .stApp { background-color: #262626; color: white; }
        [data-testid="stSidebar"] { background-color: #3399ff; color: white; }
        </style>
        """,
        unsafe_allow_html=True
    )

    df = pd.read_csv(DATA_FILE)
    df['Customer Type'] = df['Customer Type'].fillna('Buyer (Jewelry)').replace('', 'Buyer (Jewelry)')
    df['Date'] = pd.to_datetime(df['Date'])
    df['Grade'] = df['Grade'].fillna('Unknown').astype(str)
    df['True Spend'] = df['Price (CAD)'] - df['Discount (CAD)'] + df['Shipping (CAD)'] + df['Taxes Collected (CAD)']

    # Sidebar Filters
    st.sidebar.title("Filters")
    countries = sorted(df['Country'].dropna().unique())
    selected_country = st.sidebar.multiselect("Select Country", countries, default=[])
    customer_types = sorted(df['Customer Type'].dropna().unique())
    selected_type = st.sidebar.multiselect("Select Customer Type", customer_types, default=[])
    grades = sorted(df['Grade'].dropna().unique())
    selected_grade = st.sidebar.multiselect("Select Grade", grades, default=[])
    df['YearMonth'] = df['Date'].dt.to_period('M').astype(str)
    months = sorted(df['YearMonth'].dropna().unique())
    selected_month = st.sidebar.multiselect("Select Month (YYYY-MM)", months, default=[])

    filtered_df = df.copy()
    if selected_country:
        filtered_df = filtered_df[filtered_df['Country'].isin(selected_country)]
    if selected_type:
        filtered_df = filtered_df[filtered_df['Customer Type'].isin(selected_type)]
    if selected_grade:
        filtered_df = filtered_df[filtered_df['Grade'].isin(selected_grade)]
    if selected_month:
        filtered_df = filtered_df[filtered_df['YearMonth'].isin(selected_month)]

    st.markdown("<h1 style='color:#3399ff;'>Customer Segmentation Dashboard</h1>", unsafe_allow_html=True)

    total_revenue = filtered_df['True Spend'].sum()
    total_orders = filtered_df.shape[0]
    avg_order_value = filtered_df['True Spend'].mean() if total_orders > 0 else 0
    unique_customers = filtered_df['Customer Type'].nunique()
    repeat_rate = filtered_df.groupby('Customer Type')['Sale ID'].nunique().mean() if 'Sale ID' in filtered_df.columns else 0

    top_row = st.columns(4)
    with top_row[0]:
        st.metric("Total Revenue", f"${total_revenue:,.2f}")
    with top_row[1]:
        st.metric("Total Orders", total_orders)
    with top_row[2]:
        st.metric("Avg Order Value", f"${avg_order_value:,.2f}")
    with top_row[3]:
        st.metric("Unique Customer Types", unique_customers)

    if 'Sale ID' in filtered_df.columns:
        customer_order_counts = filtered_df.groupby('Customer Type')['Sale ID'].nunique().reset_index()
        repeat_customers = customer_order_counts[customer_order_counts['Sale ID'] > 1].shape[0]
        total_customers = customer_order_counts.shape[0]
        repeat_rate = repeat_customers / total_customers if total_customers > 0 else 0
    else:
        repeat_rate = 0

    st.markdown(f"<h3 style='color:#ffcc00;'>Repeat Purchase Rate: {repeat_rate:.2%}</h3>", unsafe_allow_html=True)

    chart_row = st.columns(2)
    with chart_row[0]:
        revenue_by_customer_type = filtered_df.groupby('Customer Type')['True Spend'].sum().reset_index()
        revenue_by_customer_type = revenue_by_customer_type.sort_values(by='True Spend', ascending=False)
        fig1 = px.bar(
            revenue_by_customer_type,
            x='Customer Type',
            y='True Spend',
            title='Revenue by Customer Type',
            labels={'True Spend': 'Total Revenue (CAD)'},
            color='True Spend',
            color_continuous_scale='Blues',
            text_auto='.2s'
        )
        fig1.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig1, use_container_width=True)

    with chart_row[1]:
        avg_spend_by_customer_type = filtered_df.groupby('Customer Type')['True Spend'].mean().reset_index()
        avg_spend_by_customer_type = avg_spend_by_customer_type.sort_values(by='True Spend', ascending=False)
        fig2 = px.bar(
            avg_spend_by_customer_type,
            x='Customer Type',
            y='True Spend',
            title='Average Order Value by Customer Type',
            labels={'True Spend': 'Average Order Value (CAD)'},
            color='True Spend',
            color_continuous_scale='Viridis',
            text_auto='.2s'
        )
        fig2.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("---")
    st.subheader("Monthly Revenue Trends by Customer Type")
    filtered_df['YearMonth'] = filtered_df['Date'].dt.to_period('M').astype(str)
    monthly_revenue = filtered_df.groupby(['YearMonth', 'Customer Type'])['True Spend'].sum().reset_index()
    fig3 = px.line(
        monthly_revenue,
        x='YearMonth',
        y='True Spend',
        color='Customer Type',
        markers=True,
        title='Monthly Revenue by Customer Type',
        labels={'True Spend': 'Revenue (CAD)', 'YearMonth': 'Month'}
    )
    fig3.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig3, use_container_width=True)

    st.markdown("---")
    st.subheader("Customer Lifetime Value (CLV) Estimation")
    if 'Sale ID' in filtered_df.columns:
        key_customer_data = filtered_df.groupby('Customer Type').agg(
            Total_Revenue=('True Spend', 'sum'),
            Order_Count=('Sale ID', 'nunique')
        ).reset_index()
        key_customer_data['Avg_Order_Value'] = key_customer_data['Total_Revenue'] / key_customer_data['Order_Count']
        avg_repeat_rate = repeat_rate if repeat_rate > 0 else 0.2
        key_customer_data['Estimated_CLV'] = key_customer_data['Avg_Order_Value'] * (1 / (1 - avg_repeat_rate))

        fig4 = px.bar(
            key_customer_data,
            x='Customer Type',
            y='Estimated_CLV',
            title='Estimated Customer Lifetime Value by Customer Type',
            labels={'Estimated_CLV': 'Estimated CLV (CAD)'},
            color='Estimated_CLV',
            color_continuous_scale='Plasma',
            text_auto='.2s'
        )
        fig4.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig4, use_container_width=True)
    else:
        st.info("Sale ID column is missing, cannot calculate CLV.")

    st.markdown("---")
    st.subheader("Customer Segmentation by Grade and Type")
    grade_segment = filtered_df.groupby(['Customer Type', 'Grade'])['True Spend'].sum().reset_index()
    fig5 = px.treemap(
        grade_segment,
        path=['Customer Type', 'Grade'],
        values='True Spend',
        color='True Spend',
        color_continuous_scale='RdBu',
        title="Revenue Distribution by Customer Type & Grade"
    )
    st.plotly_chart(fig5, use_container_width=True)

    st.markdown("---")
    st.subheader("Customer Revenue Concentration (Pareto 80/20)")
    revenue_by_customer = filtered_df.groupby('Customer Type')['True Spend'].sum().reset_index()
    revenue_by_customer = revenue_by_customer.sort_values(by='True Spend', ascending=False)
    revenue_by_customer['Cumulative_Revenue'] = revenue_by_customer['True Spend'].cumsum()
    total_revenue = revenue_by_customer['True Spend'].sum()
    revenue_by_customer['Revenue_Share'] = revenue_by_customer['True Spend'] / total_revenue
    revenue_by_customer['Cumulative_Share'] = revenue_by_customer['Revenue_Share'].cumsum()
    revenue_by_customer['Customer_Rank'] = range(1, len(revenue_by_customer) + 1)
    revenue_by_customer['Customer_Percentile'] = revenue_by_customer['Customer_Rank'] / len(revenue_by_customer)

    fig6 = px.line(
        revenue_by_customer,
        x='Customer_Percentile',
        y='Cumulative_Share',
        title='Customer Revenue Concentration (Pareto Curve)',
        labels={'Customer_Percentile': 'Customer Percentile', 'Cumulative_Share': 'Cumulative Revenue Share'}
    )
    fig6.add_hline(y=0.8, line_dash="dash", line_color="red")
    fig6.add_vline(x=0.2, line_dash="dash", line_color="red")
    st.plotly_chart(fig6, use_container_width=True)

    st.markdown("---")
    st.subheader("Time-Series Revenue Forecast (Prophet Model)")
    time_series = filtered_df.groupby('Date')['True Spend'].sum().reset_index()
    time_series = time_series.rename(columns={'Date': 'ds', 'True Spend': 'y'})

    if len(time_series) > 5:
        model = Prophet(yearly_seasonality=True, weekly_seasonality=False, daily_seasonality=False)
        model.fit(time_series)
        future = model.make_future_dataframe(periods=30, freq='D')
        forecast = model.predict(future)

        forecast_fig = go.Figure()
        forecast_fig.add_trace(go.Scatter(x=time_series['ds'], y=time_series['y'], mode='lines', name='Historical'))
        forecast_fig.add_trace(go.Scatter(x=forecast['ds'], y=forecast['yhat'], mode='lines', name='Forecast'))
        forecast_fig.update_layout(title="30-Day Revenue Forecast", xaxis_title="Date", yaxis_title="Revenue (CAD)")
        st.plotly_chart(forecast_fig, use_container_width=True)
    else:
        st.info("Not enough data for forecasting.")

    st.markdown("---")
    st.subheader("Predictive Modeling: Order Count vs. Average Order Value")
    if 'Sale ID' in filtered_df.columns:
        cust_metrics = filtered_df.groupby('Customer Type').agg(
            Order_Count=('Sale ID', 'nunique'),
            Total_Spend=('True Spend', 'sum')
        ).reset_index()
        cust_metrics['Avg_Order_Value'] = cust_metrics['Total_Spend'] / cust_metrics['Order_Count']

        X = cust_metrics[['Order_Count']]
        y = cust_metrics['Avg_Order_Value']
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        reg_model = LinearRegression()
        reg_model.fit(X_scaled, y)
        cust_metrics['Predicted_AOV'] = reg_model.predict(X_scaled)

        reg_fig = px.scatter(
            cust_metrics,
            x='Order_Count',
            y='Avg_Order_Value',
            trendline='ols',
            title='Order Count vs Average Order Value by Customer Type',
            labels={'Order_Count': 'Order Count', 'Avg_Order_Value': 'Average Order Value (CAD)'}
        )
        st.plotly_chart(reg_fig, use_container_width=True)
    else:
        st.info("Sale ID column missing – cannot build regression model.")

    st.markdown("---")
    st.subheader("Customer Heatmap: Country vs. Customer Type")
    heatmap_data = filtered_df.pivot_table(
        index='Country',
        columns='Customer Type',
        values='True Spend',
        aggfunc='sum',
        fill_value=0
    )
    heatmap_fig = px.imshow(
        heatmap_data,
        labels=dict(x="Customer Type", y="Country", color="Revenue (CAD)"),
        x=heatmap_data.columns,
        y=heatmap_data.index,
        aspect='auto',
        color_continuous_scale='Blues',
        title='Revenue Heatmap: Country vs Customer Type'
    )
    st.plotly_chart(heatmap_fig, use_container_width=True)

    st.markdown("---")
    st.subheader("Cumulative Revenue Over Time")
    time_df = filtered_df.groupby('Date')['True Spend'].sum().reset_index()
    time_df = time_df.sort_values(by='Date')
    time_df['Cumulative_Revenue'] = time_df['True Spend'].cumsum()
    cum_fig = px.area(
        time_df,
        x='Date',
        y='Cumulative_Revenue',
        title='Cumulative Revenue Over Time',
        labels={'Cumulative_Revenue': 'Cumulative Revenue (CAD)', 'Date': 'Date'}
    )
    st.plotly_chart(cum_fig, use_container_width=True)

    st.markdown("---")
    st.subheader("Customer Type Breakdown Summary")
    cust_summary = filtered_df.groupby('Customer Type').agg(
        Total_Revenue=('True Spend', 'sum'),
        Order_Count=('Sale ID', 'nunique') if 'Sale ID' in filtered_df.columns else ('True Spend', 'count'),
        Average_Order_Value=('True Spend', 'mean')
    ).reset_index()
    st.dataframe(cust_summary.style.format({
        'Total_Revenue': '{:,.2f}',
        'Average_Order_Value': '{:,.2f}'
    }), use_container_width=True)

    st.markdown("---")
    st.subheader("Raw Filtered Data Preview")
    st.dataframe(filtered_df.head(200), use_container_width=True)

elif page == "Geography & Channels":
    import pathlib
    import numpy as np
    import pandas as pd
    import streamlit as st
    import plotly.express as px
    import plotly.graph_objects as go
    import plotly.io as pio
    from scipy import stats

    st.markdown("""
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
    [data-testid="metric-container"] [data-testid="stMetricLabel"] { font-size: 0.85rem !important; }
    .js-plotly-plot .plot-container { width: 100% !important; }
    [data-testid="stDataFrame"] { width: 100% !important; }
    </style>
    """, unsafe_allow_html=True)

    st.title("Geography & Channel")
    st.caption("World map • Geography × Channels • Time trends + shipping lag • Stats • $ CAD")

    ESSENTIAL = [
        "Sale ID", "Date", "Country", "City", "Channel",
        "Price (CAD)", "Discount (CAD)", "Shipping (CAD)", "Taxes Collected (CAD)", "Shipped Date"
    ]

    @st.cache_data(show_spinner=False)
    def load_csv(p: pathlib.Path) -> pd.DataFrame:
        try:
            d = pd.read_csv(p)
        except Exception:
            d = pd.read_csv(p, encoding="utf-8-sig")
        d.columns = d.columns.str.strip()
        return d

    def _clean_str(s: pd.Series) -> pd.Series:
        return s.astype(str).str.strip().replace({"nan": np.nan, "None": np.nan, "": np.nan})

    def normalize_country(x: str) -> str:
        s = "" if x is None else str(x).strip()
        rep = {
            "United States": "USA",
            "U.S.A.": "USA",
            "US": "USA",
            "UK": "United Kingdom",
            "England": "United Kingdom",
        }
        return rep.get(s, s or "Unknown")

    def basic_clean(df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        df["Shipped Date"] = pd.to_datetime(df["Shipped Date"], errors="coerce")
        for c in ["Price (CAD)", "Discount (CAD)", "Shipping (CAD)", "Taxes Collected (CAD)"]:
            df[c] = pd.to_numeric(df[c], errors="coerce")
        df["Channel"] = _clean_str(df["Channel"]).fillna("Unknown")
        df["Country"] = _clean_str(df["Country"]).map(normalize_country)
        df["City"] = _clean_str(df["City"])
        df["Net Revenue"] = df["Price (CAD)"] - df["Discount (CAD)"]
        df["Total Collected"] = df["Net Revenue"] + df["Shipping (CAD)"] + df["Taxes Collected (CAD)"]
        df["Days_To_Ship"] = (df["Shipped Date"] - df["Date"]).dt.days
        return df

    df = load_csv(DATA_FILE)
    missing = [c for c in ESSENTIAL if c not in df.columns]
    if missing:
        st.error("Missing required columns: " + ", ".join(missing))
        st.stop()

    df = basic_clean(df)

    st.sidebar.subheader("Filters")
    metric = st.sidebar.selectbox(
        "Metric",
        ["Net Revenue", "Total Collected", "Price (CAD)", "Discount (CAD)", "Shipping (CAD)", "Taxes Collected (CAD)"],
        index=0
    )

    min_date = df["Date"].min()
    max_date = df["Date"].max()
    start, end = st.sidebar.date_input(
        "Date range",
        [min_date, max_date],
        min_value=min_date,
        max_value=max_date
    )

    base = df[(df["Date"] >= pd.to_datetime(start)) & (df["Date"] <= pd.to_datetime(end))].copy()
    countries = sorted([c for c in base["Country"].dropna().unique().tolist() if c])
    sel_countries = st.sidebar.multiselect("Countries", countries, default=countries)
    channels = sorted([c for c in base["Channel"].dropna().unique().tolist() if c])
    sel_channels = st.sidebar.multiselect("Channels", channels, default=channels)

    if sel_countries:
        base = base[base["Country"].isin(sel_countries)]
    if sel_channels:
        base = base[base["Channel"].isin(sel_channels)]

    cities = sorted([c for c in base["City"].dropna().unique().tolist() if c])
    sel_cities = st.sidebar.multiselect("Cities (optional)", cities, default=[])
    f = base.copy()
    if sel_cities:
        f = f[f["City"].isin(sel_cities)]

    if f.empty:
        st.warning("No rows match the current filters.")
        st.stop()

    country_totals = f.groupby("Country")[metric].sum().sort_values(ascending=False)
    channel_totals = f.groupby("Channel")[metric].sum().sort_values(ascending=False)
    top_country = country_totals.index[0] if len(country_totals) else "N/A"
    top_channel = channel_totals.index[0] if len(channel_totals) else "N/A"

    cons_rate = (f["Consignment? (Y/N)"] == "Y").mean() * 100 if "Consignment? (Y/N)" in f.columns else np.nan
    neg_lag_rows = f["Days_To_Ship"].lt(0).sum()

    tabs = st.tabs(["Overview", "World Map", "Geography × Channels", "Time", "Stats", "Data"])
    with tabs[0]:
        st.subheader("Insights")
        share_top = float(country_totals.iloc[0] / country_totals.sum()) if country_totals.sum() else np.nan
        bullets = []
        if np.isfinite(share_top):
            bullets.append(f"- **{top_country}** is the biggest market and drives about **{share_top*100:.1f}%** of {metric}.")
        bullets.append(f"- The top channel by {metric} is **{top_channel}**.")
        if np.isfinite(cons_rate):
            bullets.append(f"- Consignment is **{cons_rate:.1f}%** of orders.")
        if neg_lag_rows > 0:
            bullets.append(f"- Shipping data has **{neg_lag_rows}** rows where ship date is before sale date.")
        st.markdown("\n".join(bullets) if bullets else "-")

    with tabs[1]:
        st.subheader(f"World map - {metric} ($ CAD)")
        agg = country_totals.reset_index().rename(columns={metric: "value"})
        agg["share"] = agg["value"] / agg["value"].sum()
        fig = px.choropleth(
            agg,
            locations="Country",
            locationmode="country names",
            color="value",
            hover_name="Country",
            custom_data=["share"],
            projection="natural earth",
        )
        fig.update_traces(
            hovertemplate="<b>%{hovertext}</b><br>Value: %{z:,.0f}<br>Share: %{customdata[0]:.1%}<extra></extra>"
        )
        fig.update_layout(margin=dict(l=0, r=0, t=40, b=0))
        st.plotly_chart(fig, use_container_width=True)

    with tabs[2]:
        st.subheader(f"{metric} by Country × Channel")
        pivot = f.pivot_table(index="Country", columns="Channel", values=metric, aggfunc="sum", fill_value=0)
        fig = px.imshow(
            pivot,
            labels=dict(x="Channel", y="Country", color=metric),
            aspect="auto"
        )
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(pivot, use_container_width=True)

    with tabs[3]:
        st.subheader(f"Time trends for {metric}")
        ts = f.groupby("Date")[metric].sum().reset_index()
        fig = px.line(ts, x="Date", y=metric, markers=True)
        st.plotly_chart(fig, use_container_width=True)

        if "Days_To_Ship" in f.columns:
            st.subheader("Shipping delay vs metric")
            lag_df = f.dropna(subset=["Days_To_Ship"])
            fig2 = px.scatter(
                lag_df,
                x="Days_To_Ship",
                y=metric,
                color="Country",
                trendline="ols"
            )
            st.plotly_chart(fig2, use_container_width=True)

    with tabs[4]:
        st.subheader("Descriptive statistics")
        st.write(f[[metric, "Country", "Channel"]].describe(include="all"))

    with tabs[5]:
        st.subheader("Filtered data")
        st.dataframe(f.head(200), use_container_width=True)
        st.download_button(
            "Download filtered data (CSV)",
            data=f.to_csv(index=False).encode("utf-8"),
            file_name="filtered_data.csv",
            mime="text/csv"
        )

elif page == "Price Drivers & Correlations":
    import streamlit as st
    import pandas as pd
    import plotly.express as px

    df = pd.read_csv(DATA_FILE)

    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')

    for col in ['Discount (CAD)', 'Shipping (CAD)', 'Taxes Collected (CAD)']:
        if col in df.columns:
            df[col] = df[col].fillna(0)

    df['Net_Sale_Value'] = df['Price (CAD)']
    if 'Discount (CAD)' in df.columns:
        df['Net_Sale_Value'] = df['Net_Sale_Value'] - df['Discount (CAD)']
    if 'Shipping (CAD)' in df.columns:
        df['Net_Sale_Value'] = df['Net_Sale_Value'] + df['Shipping (CAD)']
    if 'Taxes Collected (CAD)' in df.columns:
        df['Net_Sale_Value'] = df['Net_Sale_Value'] + df['Taxes Collected (CAD)']

    if 'Date' in df.columns:
        df['YearMonth'] = df['Date'].dt.to_period('M').astype(str)

    st.header("Price Drivers & Correlation Analysis")

    if 'Country' in df.columns and 'Sale ID' in df.columns:
        group = (
            df.groupby('Country', as_index=False)
              .agg(
                  Avg_Price=('Price (CAD)', 'mean'),
                  Median_Price=('Price (CAD)', 'median'),
                  Num_Sales=('Sale ID', 'count')
              )
              .sort_values('Num_Sales', ascending=False)
        )
        fig = px.bar(group.head(15),
                     x='Country',
                     y='Avg_Price',
                     hover_data=['Median_Price', 'Num_Sales'],
                     title='Average Price by Country (Top 15 by # of Sales)')
        fig.update_layout(xaxis_title='Country', yaxis_title='Average Price (CAD)')
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(group.head(20), use_container_width=True)
    else:
        st.write("Required columns 'Country' and/or 'Sale ID' are missing.")

    if 'Grade' in df.columns:
        fig = px.box(df,
                     x='Grade',
                     y='Price (CAD)',
                     points='all',
                     title='Price Distribution by Grade')
        fig.update_layout(xaxis_title='Grade', yaxis_title='Price (CAD)')
        st.plotly_chart(fig, use_container_width=True)

        stats_table = (
            df.groupby('Grade')['Price (CAD)']
              .describe()[['count', 'mean', 'std', 'min', '25%', '50%', '75%', 'max']]
        )
        st.dataframe(stats_table, use_container_width=True)
    else:
        st.write("Column 'Grade' is missing.")

    if 'Color Count (#)' in df.columns:
        fig = px.scatter(df,
                         x='Color Count (#)',
                         y='Price (CAD)',
                         title='Color Count vs. Price',
                         trendline='ols',
                         hover_data=['Grade'] if 'Grade' in df.columns else None)
        fig.update_layout(xaxis_title='Color Count (#)', yaxis_title='Price (CAD)')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.write("Column 'Color Count (#)' is missing.")

    if 'length' in df.columns and 'width' in df.columns and 'Price (CAD)' in df.columns:
        df['Area'] = df['length'] * df['width']
        fig = px.scatter(df,
                         x='Area',
                         y='Price (CAD)',
                         title='Area vs. Price',
                         hover_data=['Grade', 'Product Type'] if 'Product Type' in df.columns else ['Grade'])
        fig.update_layout(xaxis_title='Area (length × width)', yaxis_title='Price (CAD)')
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(df[['length', 'width', 'Area', 'Price (CAD)']].head(30), use_container_width=True)
    else:
        st.write("Columns for length/width/price are missing for Area vs Price.")

    if 'Net_Sale_Value' in df.columns:
        fig = px.histogram(df,
                           x='Net_Sale_Value',
                           nbins=40,
                           title='Distribution of Net Sale Value')
        fig.update_layout(xaxis_title='Net Sale Value (CAD)', yaxis_title='Count')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.write("Column 'Net_Sale_Value' is missing.")

    if 'Date' in df.columns and 'Net_Sale_Value' in df.columns:
        monthly = (
            df.groupby('YearMonth', as_index=False)
              .agg(
                  Total_Net_Sales=('Net_Sale_Value', 'sum'),
                  Avg_Net_Sales=('Net_Sale_Value', 'mean'),
                  Num_Transactions=('Sale ID', 'count') if 'Sale ID' in df.columns else ('Net_Sale_Value', 'count')
              )
        )
        fig = px.line(monthly,
                      x='YearMonth',
                      y='Total_Net_Sales',
                      title='Total Net Sales Over Time',
                      markers=True)
        fig.update_layout(xaxis_title='Year-Month', yaxis_title='Total Net Sales (CAD)')
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(monthly.head(24), use_container_width=True)
    else:
        st.write("Could not compute monthly Net_Sale_Value due to missing columns.")

    if 'Shipping (CAD)' in df.columns and 'Price (CAD)' in df.columns:
        ship_df = df[df['Shipping (CAD)'] > 0].copy()
        if not ship_df.empty:
            fig = px.scatter(ship_df,
                             x='Shipping (CAD)',
                             y='Price (CAD)',
                             title='Shipping Cost vs Price',
                             hover_data=[c for c in ['Product Type', 'Country', 'Customer Type'] if c in ship_df.columns])
            fig.update_layout(xaxis_title='Shipping (CAD)', yaxis_title='Price (CAD)')
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(ship_df[['Shipping (CAD)', 'Price (CAD)']].head(30), use_container_width=True)
        else:
            st.write("No rows with positive shipping cost.")
    else:
        st.write("Column 'Shipping (CAD)' is missing.")

elif page == "Overall Sales EDA":
    import streamlit as st
    import pandas as pd
    import numpy as np
    import matplotlib.pyplot as plt

    df = pd.read_csv(DATA_FILE)

    df.head()

    if "Date" in df.columns and "Shipped Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        df["Shipped Date"] = pd.to_datetime(df["Shipped Date"], errors="coerce")
        df["Days_To_Ship"] = (df["Shipped Date"] - df["Date"]).dt.days

    df["Net Revenue"] = df["Price (CAD)"] - df["Discount (CAD)"]
    df.rename(columns={"weight": "Weight", "width": "Width", "length": "Length"}, inplace=True)

    df.head()
    df.describe()
    rev_by_type = df.groupby("Product Type")["Net Revenue"].sum().sort_values()

    st.header("Dinosty 2025 – Overall Sales EDA")

    plt.figure(figsize=(10, 6))
    rev_by_type.plot(kind="barh", color="teal")
    plt.title("Revenue by Product Type")
    plt.xlabel("Total Net Revenue (CAD)")
    plt.ylabel("Product Type")
    st.pyplot(plt.gcf())

    rev_type_grade = df.pivot_table(
        index="Product Type",
        columns="Grade",
        values="Net Revenue",
        aggfunc="sum",
        fill_value=0
    )

    plt.figure(figsize=(12, 7))
    rev_type_grade.plot(kind="bar", stacked=True, figsize=(12, 7), colormap="tab20")
    plt.title("Revenue by Product Type and Grade")
    plt.xlabel("Product Type")
    plt.ylabel("Total Net Revenue (CAD)")
    plt.legend(title="Grade")
    plt.xticks(rotation=45)
    st.pyplot(plt.gcf())

    plt.figure(figsize=(12, 6))
    df.boxplot(column="Price (CAD)", by="Product Type", grid=False, rot=45)
    plt.title("Price Distribution by Product Type")
    plt.suptitle("")
    plt.xlabel("Product Type")
    plt.ylabel("Price (CAD)")
    st.pyplot(plt.gcf())

    if "Days_To_Ship" in df.columns:
        plt.figure(figsize=(10, 6))
        plt.scatter(df["Days_To_Ship"], df["Net Revenue"], alpha=0.6, color="teal")
        plt.title("Shipping Time vs. Net Revenue")
        plt.xlabel("Days to Ship")
        plt.ylabel("Net Revenue (CAD)")

        clean = df.dropna(subset=["Days_To_Ship", "Net Revenue"])
        if not clean.empty:
            z = np.polyfit(clean["Days_To_Ship"], clean["Net Revenue"], 1)
            p = np.poly1d(z)
            x_vals = np.linspace(clean["Days_To_Ship"].min(), clean["Days_To_Ship"].max(), 100)
            plt.plot(x_vals, p(x_vals), color="red")

        st.pyplot(plt.gcf())
    else:
        st.info("Days_To_Ship column not available; cannot plot shipping vs revenue.")
