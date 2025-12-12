#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import streamlit as st

# Global page configuration for the combined app
st.set_page_config(page_title="Dinosty 2025 • Full Analytics Suite", layout="wide")

st.sidebar.title("Dinosty 2025 Analytics Suite")
page = st.sidebar.radio(
    "Select a dashboard",
    (
        "Customer Segmentation",
        "Geography & Channels",
        "Price Drivers & Correlations",
        "Dinosty 2025 Overall Sales"
    )
)

if page == "Customer Segmentation":
    import pandas as pd
    import plotly.graph_objects as go
    import streamlit as st
    import plotly.express as px
    from prophet import Prophet
    from sklearn.linear_model import LinearRegression
    from sklearn.preprocessing import StandardScaler

    # st.set_page_config(page_title="Customer Segmentation Dashboard", layout="wide")  # (disabled here; config set at top of combined app)

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
    df = pd.read_csv(r'C:\Users\jasph\Downloads\Combined_Sales_2025.csv')
    df['Customer Type'] = df['Customer Type'].fillna('Buyer (Jewelry)').replace('', 'Buyer (Jewelry)')
    df['Date'] = pd.to_datetime(df['Date'])
    df['Grade'] = df['Grade'].fillna('Unknown').astype(str)
    df['True Spend'] = df['Price (CAD)'] - df['Discount (CAD)'] + df['Shipping (CAD)'] + df['Taxes Collected (CAD)']

    # --- SIDEBAR ---
    st.sidebar.title("Filters")
    # Country filter
    countries = sorted(df['Country'].dropna().unique())
    selected_country = st.sidebar.multiselect("Select Country", countries, default=[])
    # Customer Type filter
    customer_types = sorted(df['Customer Type'].dropna().unique())
    selected_type = st.sidebar.multiselect("Select Customer Type", customer_types, default=[])

    # Grade filter
    grades = sorted(df['Grade'].dropna().unique())
    selected_grade = st.sidebar.multiselect("Select Grade", grades, default=[])

    # Month filter
    df['YearMonth'] = df['Date'].dt.to_period('M').astype(str)
    months = sorted(df['YearMonth'].dropna().unique())
    selected_month = st.sidebar.multiselect("Select Month (YYYY-MM)", months, default=[])

    # Filter dataset based on selections
    filtered_df = df.copy()
    if selected_country:
        filtered_df = filtered_df[filtered_df['Country'].isin(selected_country)]
    if selected_type:
        filtered_df = filtered_df[filtered_df['Customer Type'].isin(selected_type)]
    if selected_grade:
        filtered_df = filtered_df[filtered_df['Grade'].isin(selected_grade)]
    if selected_month:
        filtered_df = filtered_df[filtered_df['YearMonth'].isin(selected_month)]

    # --- DASHBOARD TITLE ---
    st.title("Customer Segmentation Dashboard")

    # --- TOP METRICS ---
    total_revenue = filtered_df['True Spend'].sum()
    total_orders = filtered_df.shape[0]
    avg_order_value = filtered_df['True Spend'].mean() if total_orders > 0 else 0
    unique_customers = filtered_df['Customer Type'].nunique()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Revenue", f"${total_revenue:,.2f}")
    col2.metric("Total Orders", total_orders)
    col3.metric("Avg Order Value", f"${avg_order_value:,.2f}")
    col4.metric("Unique Customer Types", unique_customers)

    # --- VISUALIZATIONS ---

    # 1. Revenue by Customer Type
    st.subheader("Revenue by Customer Type")
    revenue_by_customer = filtered_df.groupby('Customer Type')['True Spend'].sum().reset_index()
    fig1 = px.bar(
        revenue_by_customer,
        x='Customer Type',
        y='True Spend',
        title='Total Revenue by Customer Type',
        labels={'True Spend': 'Revenue (CAD)'},
        text_auto='.2s'
    )
    fig1.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig1, use_container_width=True)

    # 2. Monthly Revenue Trend
    st.subheader("Monthly Revenue Trend")
    monthly_revenue = filtered_df.groupby('YearMonth')['True Spend'].sum().reset_index()
    fig2 = px.line(
        monthly_revenue,
        x='YearMonth',
        y='True Spend',
        markers=True,
        title='Monthly Revenue Trend'
    )
    fig2.update_layout(xaxis_title='Month', yaxis_title='Revenue (CAD)')
    st.plotly_chart(fig2, use_container_width=True)

    # 3. Customer Segmentation by Grade and Customer Type
    st.subheader("Customer Segmentation by Grade & Customer Type")
    segmentation = filtered_df.groupby(['Customer Type', 'Grade'])['True Spend'].sum().reset_index()
    fig3 = px.treemap(
        segmentation,
        path=['Customer Type', 'Grade'],
        values='True Spend',
        title='Revenue Distribution by Customer Type and Grade'
    )
    st.plotly_chart(fig3, use_container_width=True)

    # 4. Time Series Forecasting (Prophet)
    st.subheader("Revenue Forecasting (Prophet Model)")
    time_series = filtered_df.groupby('Date')['True Spend'].sum().reset_index()
    time_series = time_series.rename(columns={'Date': 'ds', 'True Spend': 'y'})

    if len(time_series) > 2:
        model = Prophet()
        model.fit(time_series)

        future = model.make_future_dataframe(periods=30)
        forecast = model.predict(future)

        fig4 = go.Figure()
        fig4.add_trace(go.Scatter(x=time_series['ds'], y=time_series['y'], mode='lines', name='Historical'))
        fig4.add_trace(go.Scatter(x=forecast['ds'], y=forecast['yhat'], mode='lines', name='Forecast'))
        fig4.update_layout(title="30-Day Revenue Forecast", xaxis_title="Date", yaxis_title="Revenue (CAD)")
        st.plotly_chart(fig4, use_container_width=True)
    else:
        st.info("Not enough data points for forecasting.")

    # 5. Predictive Modeling: Simple Linear Regression
    st.subheader("Predictive Insights: AOV vs. Number of Orders (Dummy Example)")
    # Creating a dummy example as the dataset might not have customer-level order count directly.
    customer_revenue = filtered_df.groupby('Customer Type')['True Spend'].sum().reset_index()
    customer_revenue['Order_Count'] = filtered_df.groupby('Customer Type')['True Spend'].count().values
    customer_revenue['AOV'] = customer_revenue['True Spend'] / customer_revenue['Order_Count']

    # Preparing data for regression
    X = customer_revenue[['Order_Count']]
    y = customer_revenue['AOV']
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    reg_model = LinearRegression()
    reg_model.fit(X_scaled, y)

    customer_revenue['Predicted_AOV'] = reg_model.predict(X_scaled)

    fig5 = px.scatter(
        customer_revenue,
        x='Order_Count',
        y='AOV',
        trendline='ols',
        title='Order Count vs. Average Order Value'
    )
    st.plotly_chart(fig5, use_container_width=True)

    st.write("**Note:** This is a simplified example of predictive modeling using aggregate data.")

    # --- RAW DATA TABLE ---
    st.subheader("Filtered Data Preview")
    st.dataframe(filtered_df.head(100))


elif page == "Geography & Channels":
    import pathlib
    import numpy as np
    import pandas as pd
    import streamlit as st
    import plotly.express as px
    import plotly.graph_objects as go
    import plotly.io as pio
    from scipy import stats

    # Page config & global styles...............................

    # st.set_page_config(page_title="Week 10 • Geography & Channels", layout="wide")  # (disabled here; config set at top of combined app)

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

    st.title("Geography & Channels – Global Sales 2025")

    path = pathlib.Path(__file__).parent
    # Adjust path as needed for deployment
    csv_path = path / "Combined_Sales_2025.csv"
    df = pd.read_csv(csv_path)

    # Basic cleaning
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df["Price (CAD)"] = pd.to_numeric(df["Price (CAD)"], errors="coerce")
    df["Discount (CAD)"] = pd.to_numeric(df["Discount (CAD)"], errors="coerce")
    df["Shipping (CAD)"] = pd.to_numeric(df["Shipping (CAD)"], errors="coerce")
    df["Taxes Collected (CAD)"] = pd.to_numeric(df["Taxes Collected (CAD)"], errors="coerce")
    df["Channel"] = df["Channel"].fillna("Unknown")
    df["Country"] = df["Country"].fillna("Unknown")
    df["City"] = df["City"].fillna("Unknown")

    df["Net Revenue"] = df["Price (CAD)"] - df["Discount (CAD)"]
    df["Total Collected"] = df["Net Revenue"] + df["Shipping (CAD)"] + df["Taxes Collected (CAD)"]

    # Shipping lag in days
    df["Shipped Date"] = pd.to_datetime(df["Shipped Date"], errors="coerce")
    df["Days_To_Ship"] = (df["Shipped Date"] - df["Date"]).dt.days

    # Sidebar filters
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

    # Basic aggregations
    country_totals = f.groupby("Country")[metric].sum().sort_values(ascending=False)
    channel_totals = f.groupby("Channel")[metric].sum().sort_values(ascending=False)
    top_country = country_totals.index[0] if len(country_totals) else "N/A"
    top_channel = channel_totals.index[0] if len(channel_totals) else "N/A"

    cons_rate = (f["Consignment? (Y/N)"] == "Y").mean() * 100 if "Consignment? (Y/N)".replace(" ", "") in "".join(f.columns) else np.nan
    neg_lag_rows = f["Days_To_Ship"].lt(0).sum()

    # Tabs
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
    import pandas as pd
    import plotly.express as px

    data_path = "Combined_Sales_2025-2.csv"
    df = pd.read_csv(data_path)

    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')

    for col in ['Discount (CAD)', 'Shipping (CAD)', 'Taxes Collected (CAD)']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    if 'Price (CAD)' in df.columns and 'Discount (CAD)' in df.columns:
        df['Net_Sale_Value'] = df['Price (CAD)'] - df['Discount (CAD)']

    if 'Shipping (CAD)' in df.columns and 'Net_Sale_Value' in df.columns:
        df['Final_Collected_Value'] = df['Net_Sale_Value'] + df['Shipping (CAD)']

    if 'Taxes Collected (CAD)' in df.columns and 'Final_Collected_Value' in df.columns:
        df['Final_Collected_Value'] = df['Final_Collected_Value'] + df['Taxes Collected (CAD)']

    if 'Date' in df.columns and 'Shipped Date' in df.columns:
        df['Shipped Date'] = pd.to_datetime(df['Shipped Date'], errors='coerce')
        df['Days_To_Ship'] = (df['Shipped Date'] - df['Date']).dt.days

    st.header("Price Drivers & Correlation Analysis")

    # Correlation heatmap
    numeric_cols = [
        'Price (CAD)',
        'Net_Sale_Value',
        'Final_Collected_Value',
        'Color Count (#)',
        'Discount (CAD)',
        'Shipping (CAD)',
        'Taxes Collected (CAD)',
        'length',
        'width',
        'weight',
        'Days_To_Ship'
    ]
    numeric_cols = [c for c in numeric_cols if c in df.columns]

    if len(numeric_cols) >= 2:
        corr = df[numeric_cols].corr()
        fig = px.imshow(
            corr,
            text_auto=False,
            title="Correlation Heatmap – Price Drivers & Operational Metrics"
        )
        st.plotly_chart(fig, use_container_width=True)

    # Price vs Shipping
    if 'Shipping (CAD)' in df.columns and 'Price (CAD)' in df.columns:
        st.subheader("Price vs Shipping Cost")
        ship_df = df[df['Shipping (CAD)'] > 0]
        if not ship_df.empty:
            fig2 = px.scatter(
                ship_df,
                x='Shipping (CAD)',
                y='Price (CAD)',
                title='Shipping Cost vs. Price',
                trendline='ols'
            )
            st.plotly_chart(fig2, use_container_width=True)

    # Simple distributions
    if 'Price (CAD)' in df.columns:
        st.subheader("Price Distribution")
        fig3 = px.histogram(df, x='Price (CAD)', nbins=40, title="Price Distribution")
        st.plotly_chart(fig3, use_container_width=True)

    if 'Final_Collected_Value' in df.columns:
        st.subheader("Final Collected Value Distribution")
        fig4 = px.histogram(df, x='Final_Collected_Value', nbins=40, title="Final Collected Value Distribution")
        st.plotly_chart(fig4, use_container_width=True)


elif page == "Dinosty 2025 Overall Sales":
    import pandas as pd
    import numpy as np
    import matplotlib.pyplot as plt

    df = pd.read_csv("Combined_Sales_2025.csv")

    df["Net Revenue"] = df["Price (CAD)"] - df["Discount (CAD)"]
    df.rename(columns={"weight": "Weight", "width": "Width", "length": "Length"}, inplace=True)

    st.header("Dinosty 2025 – Overall Sales EDA (Notebook Logic)")

    st.write("The following visualizations are from your original notebook logic (matplotlib).")

    # Example: revenue distribution
    fig1, ax1 = plt.subplots(figsize=(10, 6))
    ax1.hist(df["Net Revenue"].dropna(), bins=40, color="teal", alpha=0.7)
    ax1.set_title("Distribution of Net Revenue")
    ax1.set_xlabel("Net Revenue (CAD)")
    ax1.set_ylabel("Frequency")
    st.pyplot(fig1)

    # Example: shipping time vs net revenue
    if "Shipped Date" in df.columns and "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        df["Shipped Date"] = pd.to_datetime(df["Shipped Date"], errors="coerce")
        df["Days_To_Ship"] = (df["Shipped Date"] - df["Date"]).dt.days

        fig2, ax2 = plt.subplots(figsize=(10, 6))
        ax2.scatter(df["Days_To_Ship"], df["Net Revenue"], alpha=0.6, color="teal")
        ax2.set_title("Shipping Time vs. Net Revenue")
        ax2.set_xlabel("Days to Ship")
        ax2.set_ylabel("Net Revenue (CAD)")

        # Trendline
        clean = df.dropna(subset=["Days_To_Ship", "Net Revenue"])
        if not clean.empty:
            z = np.polyfit(clean["Days_To_Ship"], clean["Net Revenue"], 1)
            p = np.poly1d(z)
            x_vals = np.linspace(clean["Days_To_Ship"].min(), clean["Days_To_Ship"].max(), 100)
            ax2.plot(x_vals, p(x_vals), color="red")

        st.pyplot(fig2)

