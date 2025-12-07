#!/usr/bin/env python
# coding: utf-8

# In[1]:


# ======================================================
# Global Ammolite Sales Dashboard - Full Streamlit Version
# ======================================================

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
FILE_PATH = r"C:\Users\basne\OneDrive\Desktop\Combined_Sales_2025.csv"

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
# WORLD MAP
# =====================
st.markdown("## 🌍 Revenue by Country")
if "Country" in df.columns:
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
    st.plotly_chart(fig_map, use_container_width=True)

# =====================
# COUNTRY DRILL-DOWN
# =====================
st.markdown("## Select a Country for Detailed Dashboard")
country_list = ["All"] + sorted(df["Country"].dropna().unique())
selected_country = st.selectbox("Country", country_list)

if selected_country != "All":
    country_df = df[df["Country"] == selected_country]

    st.markdown(f"## 📊 Dashboard for {selected_country}")

    # KPIs
    total_rev_c = country_df["Revenue"].sum()
    avg_order_c = country_df["Revenue"].mean()
    channels_count_c = country_df["Channel"].nunique() if "Channel" in country_df.columns else "N/A"

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Revenue", f"${total_rev_c:,.0f}")
    c2.metric("Avg Order Value", f"${avg_order_c:,.2f}")
    c3.metric("Channels", channels_count_c)

    # Revenue by Channel
    if "Channel" in country_df.columns:
        rev_channel = country_df.groupby("Channel")["Revenue"].sum().sort_values(ascending=False)
        st.markdown("### Revenue by Channel")
        st.bar_chart(rev_channel)

    # Revenue over Time
    if "Date" in country_df.columns:
        rev_time = country_df.groupby("Date")["Revenue"].sum().reset_index()
        fig_time = px.line(rev_time, x="Date", y="Revenue", title=f"Revenue Over Time - {selected_country}")
        st.plotly_chart(fig_time, use_container_width=True)

    # Product / SKU analysis
    prod_col = "Product Type" if "Product Type" in country_df.columns else ("Product" if "Product" in country_df.columns else None)
    if prod_col:
        rev_prod = country_df.groupby(prod_col)["Revenue"].sum().sort_values(ascending=False)
        st.markdown(f"### Revenue by {prod_col}")
        st.bar_chart(rev_prod)

# =====================
# GLOBAL ANALYSIS (if All selected)
# =====================
if selected_country == "All":
    st.markdown("## Global Revenue Analysis")

    # Revenue by Country (bar chart)
    if "Country" in df.columns:
        rev_country = df.groupby("Country")["Revenue"].sum().sort_values(ascending=False)
        fig, ax = plt.subplots(figsize=(10,5))
        rev_country.plot(kind="bar", ax=ax)
        ax.set_ylabel("Revenue (CAD)")
        ax.set_xlabel("")
        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()
        st.pyplot(fig)

    # Country x Channel Heatmap
    if "Country" in df.columns and "Channel" in df.columns:
        pivot = pd.pivot_table(df, values="Revenue", index="Country", columns="Channel", aggfunc="sum", fill_value=0)
        fig, ax = plt.subplots(figsize=(12,6))
        sns.heatmap(pivot, cmap="YlOrRd", linewidths=0.5, ax=ax)
        ax.set_ylabel("Revenue")
        ax.set_xlabel("Channel")
        plt.tight_layout()
        st.pyplot(fig)

    # Revenue over Time
    if "Date" in df.columns:
        ts = df.groupby("Date")["Revenue"].sum().reset_index()
        fig_time = px.line(ts, x="Date", y="Revenue", title="Revenue Over Time")
        st.plotly_chart(fig_time, use_container_width=True)

    # Product / SKU analysis
    prod_col = "Product Type" if "Product Type" in df.columns else ("Product" if "Product" in df.columns else None)
    if prod_col:
        rev_prod = df.groupby(prod_col)["Revenue"].sum().sort_values(ascending=False)
        st.markdown(f"### Revenue by {prod_col}")
        st.bar_chart(rev_prod)

# =====================
# EXECUTIVE INSIGHTS
# =====================
st.markdown("## Executive Insights & Recommendations")
st.markdown("""
- **Top-performing markets:** North America (Canada, USA)  
- **Channels performing well in Asia:** Online & Wholesale  
- **Recommendations:**  
    - Protect top markets  
    - Focus Online/Wholesale marketing in Asia  
    - Use heatmap to identify expansion opportunities
""")


# In[ ]:




