#!/usr/bin/env python
# coding: utf-8

# ======================================================
# Global Ammolite Sales Dashboard - Streamlit Full Version
# ======================================================

import pandas as pd
import numpy as np
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
from pathlib import Path
from streamlit_plotly_events import plotly_events

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

# ---------- STREAMLIT CONFIG ----------
st.set_page_config(layout="wide", page_title="Global Ammolite Sales Dashboard")
st.title("🌎 Global Ammolite Sales Dashboard")

# =====================
# GLOBAL KPIs
# =====================
total_rev = df["Revenue"].sum()
avg_order = df["Revenue"].mean()
countries_count = df["Country"].nunique() if "Country" in df.columns else "N/A"

col1, col2, col3 = st.columns(3)
col1.metric("Total Revenue", f"${total_rev:,.0f}")
col2.metric("Avg Order Value", f"${avg_order:,.2f}")
col3.metric("Countries", countries_count)

# =====================
# WORLD MAP - CLICKABLE
# =====================
st.markdown("## 🌍 Click a Country on the Map for Detailed Dashboard")

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

# Capture click events
clicked_points = plotly_events(fig_map, click_event=True, hover_event=False)
if "selected_country" not in st.session_state:
    st.session_state.selected_country = "All"

if clicked_points:
    st.session_state.selected_country = clicked_points[0]["location"]

st.plotly_chart(fig_map, use_container_width=True)

# =====================
# COUNTRY SELECTION (Dropdown fallback)
# =====================
country_list = ["All"] + sorted(df["Country"].dropna().unique())
selected_country = st.selectbox("Or select a Country", country_list, index=country_list.index(st.session_state.selected_country))

# =====================
# FILTER DATA
# =====================
if selected_country != "All":
    df_filtered = df[df["Country"] == selected_country]
else:
    df_filtered = df.copy()

# =====================
# EXPANDERS FOR GRAPHS
# =====================
# Revenue by Country (global)
with st.expander("📊 Revenue by Country"):
    if selected_country == "All":
        rev_country = df_filtered.groupby("Country")["Revenue"].sum().sort_values(ascending=False)
        fig, ax = plt.subplots(figsize=(12,6))
        rev_country.plot(kind="bar", ax=ax, color="teal")
        ax.set_ylabel("Revenue (CAD)")
        ax.set_xlabel("")
        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()
        st.pyplot(fig)
        st.markdown("""
        **Insights:**  
        North America (Canada & USA) dominates revenue, indicating strong core markets.  
        Asia has emerging potential in online and wholesale channels.  
        Europe and smaller markets show moderate performance.  

        **Recommendations:**  
        - Strengthen top-performing countries through marketing & loyalty programs.  
        - Explore expansion strategies for moderate markets.  
        - Investigate low-performing regions for untapped opportunities.
        """)

# Revenue by Channel (heatmap)
with st.expander("📈 Revenue by Country × Channel Heatmap"):
    if "Channel" in df_filtered.columns and "Country" in df_filtered.columns:
        pivot = pd.pivot_table(df_filtered, values="Revenue", index="Country", columns="Channel", aggfunc="sum", fill_value=0)
        fig, ax = plt.subplots(figsize=(12,6))
        sns.heatmap(pivot, cmap="YlOrRd", linewidths=0.5, ax=ax)
        ax.set_ylabel("Country")
        ax.set_xlabel("Channel")
        plt.tight_layout()
        st.pyplot(fig)
        st.markdown("""
        **Insights:**  
        Asia shows strong revenue in Online and Wholesale channels.  
        North America has balanced performance across channels.  
        Galleries and stores perform better in Europe.  

        **Recommendations:**  
        - Align marketing and sales strategy with channel preferences per region.  
        - Optimize e-commerce for high-online-revenue countries.  
        - Consider physical stores in regions with high in-person sales.
        """)

# Revenue Over Time
with st.expander("📅 Revenue Over Time"):
    if "Date" in df_filtered.columns:
        rev_time = df_filtered.groupby("Date")["Revenue"].sum().reset_index()
        fig_time = px.line(rev_time, x="Date", y="Revenue", title=f"Revenue Over Time - {selected_country}", markers=True)
        st.plotly_chart(fig_time, use_container_width=True)
        st.markdown("""
        **Insights:**  
        Seasonal trends may exist, showing spikes during holidays or key events.  
        Consistent growth indicates a stable market.  
        Any sudden drops may reveal operational or market challenges.  

        **Recommendations:**  
        - Plan inventory and marketing campaigns around peak periods.  
        - Investigate dips for process improvements.  
        - Monitor long-term growth trends for strategic decisions.
        """)

# Product / SKU Analysis
with st.expander("🛍️ Revenue by Product / SKU"):
    prod_col = "Product Type" if "Product Type" in df_filtered.columns else ("Product" if "Product" in df_filtered.columns else None)
    if prod_col:
        rev_prod = df_filtered.groupby(prod_col)["Revenue"].sum().sort_values(ascending=False)
        st.bar_chart(rev_prod)
        st.markdown(f"""
        **Insights:**  
        Top-selling products drive the majority of revenue.  
        Identifying best-performing SKUs can guide production and marketing.  

        **Recommendations:**  
        - Focus on high-revenue products for promotions.  
        - Analyze low-performing SKUs for potential discontinuation.  
        - Adjust inventory based on SKU performance.
        """)

# =====================
# EXECUTIVE INSIGHTS
# =====================
with st.expander("💡 Executive Insights & Recommendations"):
    st.markdown("""
    - **Top-performing markets:** North America (Canada & USA)  
    - **Channels performing well in Asia:** Online & Wholesale  
    - **Recommendations:**  
        - Protect top markets through loyalty & marketing campaigns  
        - Optimize channel strategy regionally  
        - Use heatmaps and trends to identify expansion opportunities  
        - Track seasonal patterns for planning & inventory
    """)
