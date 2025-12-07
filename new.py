#!/usr/bin/env python
# coding: utf-8

# In[4]:


# ======================================================
# FULL DATA ANALYSIS + VISUALIZATION + STREAMLIT DASHBOARD
# ======================================================

import sys
import os
from pathlib import Path
import warnings

warnings.filterwarnings("ignore")

# ---------- REQUIRED LIBRARIES ----------
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

pd.set_option("display.float_format", "{:,.2f}".format)
sns.set_style("whitegrid")

# ---------- OPTIONAL LIBRARIES ----------
HAS_SCIPY = False
HAS_SKLEARN = False
HAS_PLOTLY = False
HAS_STREAMLIT = False

try:
    from scipy import stats as _scipy_stats
    HAS_SCIPY = True
except Exception:
    _scipy_stats = None

try:
    from sklearn.linear_model import LinearRegression as _LinearRegression
    HAS_SKLEARN = True
except Exception:
    _LinearRegression = None

try:
    import plotly.express as px
    HAS_PLOTLY = True
except Exception:
    px = None

try:
    import streamlit as st
    HAS_STREAMLIT = True
except Exception:
    st = None

# ---------- CONFIG ----------
FILE_PATH = r"C:\Users\basne\OneDrive\Desktop\Combined_Sales_2025.csv"

if not Path(FILE_PATH).exists():
    if Path("Combined_Sales_2025.csv").exists():
        FILE_PATH = "Combined_Sales_2025.csv"
    else:
        raise FileNotFoundError(f"CSV not found at {Path(FILE_PATH).resolve()}")

OUTPUT_DIR = Path("analysis_outputs")
OUTPUT_DIR.mkdir(exist_ok=True)

# ---------- HELPERS ----------
def safe_read_csv(path):
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"CSV not found at {path.resolve()}")
    return pd.read_csv(path)

def savefig(fig, name):
    out = OUTPUT_DIR / name
    fig.savefig(out, bbox_inches="tight")
    print(f"Saved: {out.resolve()}")

def manual_anova(groups):
    groups = [np.asarray(g) for g in groups if len(g) > 0]
    if len(groups) < 2:
        return None, None
    all_data = np.concatenate(groups)
    grand_mean = np.mean(all_data)
    ss_between = sum(len(g) * (np.mean(g) - grand_mean) ** 2 for g in groups)
    ss_within = sum(np.sum((g - np.mean(g)) ** 2) for g in groups)
    df_between = len(groups) - 1
    df_within = len(all_data) - len(groups)
    ms_between = ss_between / df_between if df_between > 0 else np.nan
    ms_within = ss_within / df_within if df_within > 0 else np.nan
    f_stat = ms_between / ms_within if ms_within > 0 else np.nan
    return f_stat, {"ss_between": ss_between, "ss_within": ss_within, "df_between": df_between, "df_within": df_within}

def numpy_regression(x, y):
    slope, intercept = np.polyfit(np.asarray(x), np.asarray(y), 1)
    return slope, intercept

# ---------- LOAD DATA ----------
print("Loading data from:", FILE_PATH)
df = safe_read_csv(FILE_PATH)

# Strip all column names
df.columns = [c.strip() for c in df.columns]
print("Columns in CSV:", df.columns.tolist())

# ---------- CREATE REVENUE COLUMN ----------
if "Revenue" not in df.columns:
    if "Price (CAD)" in df.columns:
        df["Revenue"] = df["Price (CAD)"]
        if "Discount (CAD)" in df.columns:
            df["Revenue"] -= df["Discount (CAD)"]
        if "Shipping (CAD)" in df.columns:
            df["Revenue"] += df["Shipping (CAD)"]
        if "Taxes Collected (CAD)" in df.columns:
            df["Revenue"] += df["Taxes Collected (CAD)"]
        print("Created 'Revenue' column from Price, Discount, Shipping, Taxes.")
    else:
        raise KeyError("No Revenue column and no 'Price (CAD)' to calculate from.")

# ---------- HANDLE DATE ----------
if "Date" in df.columns:
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

print("\nData overview:")
print(df.info())

# ---------- DESCRIPTIVE STATISTICS ----------
print("\nDescriptive statistics for Revenue:")
print(df["Revenue"].describe())

# ---------- VISUAL 1: REVENUE BY COUNTRY ----------
if "Country" in df.columns:
    rev_country = df.groupby("Country")["Revenue"].sum().sort_values(ascending=False)
    fig, ax = plt.subplots(figsize=(10, 5))
    rev_country.plot(kind="bar", ax=ax)
    ax.set_title("Total Revenue by Country")
    ax.set_ylabel("Revenue")
    ax.set_xlabel("")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    savefig(fig, "revenue_by_country.png")
    plt.close(fig)
    print("Top countries by revenue:")
    print(rev_country.head(10))

# ---------- VISUAL 2: COUNTRY × CHANNEL HEATMAP ----------
if "Country" in df.columns and "Channel" in df.columns:
    pivot = pd.pivot_table(df, values="Revenue", index="Country", columns="Channel", aggfunc="sum", fill_value=0)
    fig, ax = plt.subplots(figsize=(12, 6))
    sns.heatmap(pivot, cmap="YlOrRd", linewidths=0.5, ax=ax)
    ax.set_title("Revenue Heatmap (Country × Channel)")
    plt.tight_layout()
    savefig(fig, "heatmap_country_channel.png")
    plt.close(fig)

# ---------- VISUAL 3: REVENUE OVER TIME ----------
ts = None
if "Date" in df.columns:
    ts = df.groupby("Date")["Revenue"].sum().reset_index()
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(ts["Date"], ts["Revenue"], marker="", linewidth=1)
    ax.set_title("Revenue Over Time")
    ax.set_xlabel("Date")
    ax.set_ylabel("Revenue")
    plt.tight_layout()
    savefig(fig, "revenue_over_time.png")
    plt.close(fig)

# ---------- VISUAL 4: PRODUCT / SKU ANALYSIS ----------
prod_col = None
if "Product Type" in df.columns:
    prod_col = "Product Type"
elif "Product" in df.columns:
    prod_col = "Product"

if prod_col:
    prod_rev = df.groupby(prod_col)["Revenue"].sum().sort_values(ascending=False)
    fig, ax = plt.subplots(figsize=(10, 5))
    prod_rev.plot(kind="bar", ax=ax)
    ax.set_title(f"Revenue by {prod_col}")
    ax.set_ylabel("Revenue")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    savefig(fig, f"revenue_by_{prod_col.replace(' ', '_').lower()}.png")
    plt.close(fig)

# ---------- STATISTICAL ANALYSIS ----------
if "Channel" in df.columns:
    groups = [g["Revenue"].values for _, g in df.groupby("Channel")]
    if HAS_SCIPY:
        f_stat, p_val = _scipy_stats.f_oneway(*groups)
        print("\nANOVA (scipy): F = {:.4f}, p = {:.4g}".format(f_stat, p_val))
    else:
        f_stat, meta = manual_anova(groups)
        print("\nANOVA (manual): F = {:.4f}".format(f_stat))

# Correlation matrix
numeric_df = df.select_dtypes(include=[np.number])
if numeric_df.shape[1] > 1:
    corr = numeric_df.corr()
    fig, ax = plt.subplots(figsize=(8, 6))
    sns.heatmap(corr, annot=True, cmap="coolwarm", ax=ax)
    ax.set_title("Correlation Matrix")
    plt.tight_layout()
    savefig(fig, "correlation_matrix.png")
    plt.close(fig)

# Regression: Revenue over time
if ts is not None and len(ts) >= 2:
    x = np.arange(len(ts))
    y = ts["Revenue"].values
    if HAS_SKLEARN:
        model = _LinearRegression()
        model.fit(x.reshape(-1, 1), y)
        slope = float(model.coef_[0])
        intercept = float(model.intercept_)
    else:
        slope, intercept = numpy_regression(x, y)
    print("\nRevenue trend slope: {:.6f}".format(slope))

# ---------- INSIGHTS ----------
print("\nTop-line insights:")
if "Country" in df.columns:
    top3 = rev_country.head(3)
    print("Top 3 countries by revenue:")
    for c, v in top3.items():
        print(f" - {c}: ${v:,.2f}")

if "Channel" in df.columns:
    top_channel = df.groupby("Channel")["Revenue"].sum().sort_values(ascending=False).index[0]
    print(f"Top channel: {top_channel}")

# ---------- OPTIONAL STREAMLIT DASHBOARD ----------
RUN_STREAMLIT = "--streamlit" in sys.argv
if RUN_STREAMLIT and HAS_STREAMLIT:
    st.set_page_config(layout="wide", page_title="Global Revenue Dashboard")
    st.title("Global Ammolite Sales Dashboard")
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Revenue", f"${df['Revenue'].sum():,.0f}")
    c2.metric("Avg Order Value", f"${df['Revenue'].mean():,.2f}")
    c3.metric("Countries", df["Country"].nunique() if "Country" in df.columns else "N/A")

    if HAS_PLOTLY and "Country" in df.columns:
        rev_country_df = rev_country.reset_index()
        fig1 = px.bar(rev_country_df, x="Country", y="Revenue", title="Revenue by Country")
        st.plotly_chart(fig1, use_container_width=True)
    else:
        st.image(str(OUTPUT_DIR / "revenue_by_country.png"))

    if HAS_PLOTLY and "Country" in df.columns and "Channel" in df.columns:
        fig2 = px.imshow(pivot, title="Revenue Heatmap (Country × Channel)")
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.image(str(OUTPUT_DIR / "heatmap_country_channel.png"))

    if ts is not None and HAS_PLOTLY:
        fig3 = px.line(ts, x="Date", y="Revenue", title="Revenue Over Time")
        st.plotly_chart(fig3, use_container_width=True)
    elif ts is not None:
        st.image(str(OUTPUT_DIR / "revenue_over_time.png"))

    st.markdown("""
    ### Executive Insights
    - North America drives the highest revenue.
    - Asia performs well in Online & Wholesale channels.
    - Heatmap reveals low-performing regions and expansion opportunities.
    """)

print("\nAll outputs saved in:", OUTPUT_DIR.resolve())


# In[ ]:




