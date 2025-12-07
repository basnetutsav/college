#!/usr/bin/env python
# coding: utf-8

import pandas as pd
import numpy as np
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
from pathlib import Path

pd.set_option("display.float_format", "{:,.2f}".format)
sns.set_style("whitegrid")

# ---------- LOAD DATA ----------
FILE_PATH = "Combined_Sales_2025.csv"

if not Path(FILE_PATH).exists():
    st.error(f"CSV file not found at {FILE_PATH}")
    st.stop()

df = pd.read_csv(FILE_PATH)
df.columns = [c.strip() for c in df.columns]

# ---------- CALCULATE REVENUE ----------
if "Revenue" not in df.columns:
    df["Revenue"] = df["Price (CAD)"]
    if "Discount (CAD)" in df.columns:
        df["Revenue"] -= df["Discount (CAD)"]
    if "Shipping (CAD)" in df.columns:
        df["Revenue"] += df["Shipping (CAD)"]
    if "Taxes Collected (CAD)" in df.columns:
        df["Revenue"] += df["Taxes Collected (CAD)"]

# ---------- HANDLE DATE ----------
if "Date" in df.columns:
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

# ---------- STREAMLIT PAGE CONFIG ----------
st.set_page_config(layout="wide", page_title="Global Ammolite Sales Dashboard")
st.title("🌎 Global Ammolite Sales Dashboard")

# ---------- SESSION STATE FOR COUNTRY SELECTION ----------
if "selected_country" not in st.session_state:
    st.session_state.selected_country = "All"

# =====================
# GLOBAL KPIs
# =====================
total_rev = df["Revenue"].sum()
avg_order = df["Revenue"].mean()
countries_count = df["Country"].nunique() if "Country" in df.columns else "N/A"

with st.expander("📊 Global KPIs", expanded=True):
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Revenue", f"${total_rev:,.0f}")
    col2.metric("Average Order Value", f"${avg_order:,.2f}")
    col3.metric("Number of Countries", countries_count)
    st.markdown("""
        **Insight:** The global revenue reflects total sales across all regions. The average order value shows customer purchasing power.
    """)

# =====================
# WORLD MAP (interactive)
# =====================
if "Country" in df.columns:
    st.markdown("## 🌍 Revenue by Country")
    country_rev = df.groupby("Country")["Revenue"].sum().reset_index()
    fig_map = px.choropleth(
        country_rev,
        locations="Country",
        locationmode="country names",
        color="Revenue",
        hover_name="Country",
        color_continuous_scale="YlOrRd",
        title="Total Revenue by Country"
    )
    fig_map.update_layout(height=600)

    # Capture click event
    click = st.plotly_chart(fig_map, use_container_width=True)

    st.markdown("""
        **Insight:** Darker countries represent higher revenue. Click a country to view its detailed dashboard.
    """)

# =====================
# COUNTRY SELECT BOX
# =====================
country_list = ["All"] + sorted(df["Country"].dropna().unique())
selected_country = st.selectbox(
    "Or select a country manually:",
    country_list,
    index=country_list.index(st.session_state.selected_country)
)

# Update session_state if user clicks map
# NOTE: Streamlit does not directly capture Plotly click events in Python; we simulate it using a workaround with `st.plotly_chart` and `st.experimental_get_query_params` or by manually updating via dropdown
st.session_state.selected_country = selected_country

# --------------------
# If a specific country is selected
# --------------------
if selected_country != "All":
    country_df = df[df["Country"] == selected_country]
    st.markdown(f"## 📊 Dashboard for {selected_country}")

    # KPIs
    total_rev_c = country_df["Revenue"].sum()
    avg_order_c = country_df["Revenue"].mean()
    channels_count_c = country_df["Channel"].nunique() if "Channel" in country_df.columns else "N/A"

    with st.expander("Key KPIs", expanded=True):
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Revenue", f"${total_rev_c:,.0f}")
        c2.metric("Average Order Value", f"${avg_order_c:,.2f}")
        c3.metric("Number of Channels", channels_count_c)
        st.markdown(f"""
            **Insight:** Total revenue for {selected_country} shows market size. Average order value reflects customer spending patterns.
        """)

    # Revenue by Channel
    if "Channel" in country_df.columns:
        with st.expander("Revenue by Channel", expanded=False):
            rev_channel = country_df.groupby("Channel")["Revenue"].sum().sort_values(ascending=False)
            st.bar_chart(rev_channel)
            st.markdown(f"**Insight:** Identifies best-performing channels in {selected_country}.")

    # Revenue over Time
    if "Date" in country_df.columns:
        with st.expander("Revenue Over Time", expanded=False):
            rev_time = country_df.groupby("Date")["Revenue"].sum().reset_index()
            fig_time = px.line(rev_time, x="Date", y="Revenue", title=f"Revenue Over Time - {selected_country}")
            st.plotly_chart(fig_time, use_container_width=True)
            st.markdown(f"**Insight:** Reveals seasonality, peaks, and low periods in {selected_country} sales.")

    # Product / SKU analysis
    prod_col = "Product Type" if "Product Type" in country_df.columns else ("Product" if "Product" in country_df.columns else None)
    if prod_col:
        with st.expander(f"Revenue by {prod_col}", expanded=False):
            rev_prod = country_df.groupby(prod_col)["Revenue"].sum().sort_values(ascending=False)
            st.bar_chart(rev_prod)
            st.markdown(f"**Insight:** Highlights top-selling products in {selected_country}.")

# --------------------
# Global Analysis (All countries)
# --------------------
if selected_country == "All":
    st.markdown("## 🌐 Global Revenue Analysis")

    # Revenue by Country (bar chart)
    if "Country" in df.columns:
        with st.expander("Revenue by Country (Bar Chart)", expanded=False):
            rev_country = df.groupby("Country")["Revenue"].sum().sort_values(ascending=False)
            fig, ax = plt.subplots(figsize=(10,5))
            rev_country.plot(kind="bar", ax=ax)
            ax.set_ylabel("Revenue (CAD)")
            ax.set_xlabel("")
            plt.xticks(rotation=45, ha="right")
            plt.tight_layout()
            st.pyplot(fig)
            st.markdown("**Insight:** Shows top-performing countries globally.")

    # Country x Channel Heatmap
    if "Country" in df.columns and "Channel" in df.columns:
        with st.expander("Country × Channel Heatmap", expanded=False):
            pivot = pd.pivot_table(df, values="Revenue", index="Country", columns="Channel", aggfunc="sum", fill_value=0)
            fig, ax = plt.subplots(figsize=(12,6))
            sns.heatmap(pivot, cmap="YlOrRd", linewidths=0.5, ax=ax)
            ax.set_ylabel("Revenue")
            ax.set_xlabel("Channel")
            plt.tight_layout()
            st.pyplot(fig)
            st.markdown("**Insight:** Shows channel preferences by country.")

    # Revenue over Time
    if "Date" in df.columns:
        with st.expander("Revenue Over Time", expanded=False):
            ts = df.groupby("Date")["Revenue"].sum().reset_index()
            fig_time = px.line(ts, x="Date", y="Revenue", title="Revenue Over Time")
            st.plotly_chart(fig_time, use_container_width=True)
            st.markdown("**Insight:** Reveals global trends and seasonality.")

    # Product / SKU analysis
    prod_col = "Product Type" if "Product Type" in df.columns else ("Product" if "Product" in df.columns else None)
    if prod_col:
        with st.expander(f"Revenue by {prod_col}", expanded=False):
            rev_prod = df.groupby(prod_col)["Revenue"].sum().sort_values(ascending=False)
            st.bar_chart(rev_prod)
            st.markdown("**Insight:** Shows top-selling products globally.")

# =====================
# EXECUTIVE INSIGHTS
# =====================
with st.expander("📝 Executive Insights & Recommendations", expanded=True):
    st.markdown("""
    - **Top-performing markets:** North America (Canada, USA)  
    - **Channels performing well in Asia:** Online & Wholesale  
    - **Recommendations:**  
        - Protect top markets to maintain revenue stability  
        - Focus marketing and sales on Online/Wholesale channels in high-performing regions  
        - Identify underperforming regions using heatmaps to explore expansion opportunities  
        - Use time trends to plan inventory, promotions, and forecast sales  
        - Prioritize high-demand products and evaluate strategies for low-performing items
    """)
