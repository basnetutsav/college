#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import pandas as pd
import hvplot.pandas
import panel as pn
import os

pn.extension("tabulator")

ACCENT = "#E50914"  # Netflix red

# ----------------------------------------------------------------
# Load dataset
# ----------------------------------------------------------------
possible_paths = [
    "./netflix_titles.csv",
    "/mnt/data/netflix_titles.csv",
    os.path.expanduser("~/netflix_titles.csv"),
]

path = next((p for p in possible_paths if os.path.exists(p)), None)
if not path:
    raise FileNotFoundError(
        "❌ Could not find 'netflix_titles.csv'. Please place it in the same folder as this script."
    )

df = pd.read_csv(path)

# Clean columns
df["release_year"] = pd.to_numeric(df["release_year"], errors="coerce").fillna(0).astype(int)
df["country"] = df["country"].fillna("Unknown")
df["type"] = df["type"].fillna("Unknown")

# Expand countries for filtering
df["country_list"] = df["country"].apply(lambda x: [c.strip() for c in str(x).split(",") if c.strip()])
df_expanded = df.explode("country_list")

# ----------------------------------------------------------------
# Widgets
# ----------------------------------------------------------------
type_select = pn.widgets.Select(
    name="Type",
    options=["All"] + sorted(df["type"].dropna().unique().tolist()),
    value="All"
)

countries = sorted(df_expanded["country_list"].dropna().unique().tolist())
country_select = pn.widgets.MultiSelect(
    name="Country",
    options=countries,
    value=["United States"] if "United States" in countries else [],
    size=6
)

year_slider = pn.widgets.IntRangeSlider(
    name="Release Year Range",
    start=int(df["release_year"].min()),
    end=int(df["release_year"].max()),
    value=(2000, 2020),
    step=1
)

# ----------------------------------------------------------------
# Filtering logic
# ----------------------------------------------------------------
def filter_data(type_sel, countries, year_range):
    dff = df_expanded.copy()
    if type_sel != "All":
        dff = dff[dff["type"] == type_sel]
    if countries:
        dff = dff[dff["country_list"].isin(countries)]
    dff = dff[
        (dff["release_year"] >= year_range[0]) &
        (dff["release_year"] <= year_range[1])
    ]
    return dff.drop_duplicates(subset=["title"]).reset_index(drop=True)

filtered = pn.bind(filter_data, type_select, country_select, year_slider)

# ----------------------------------------------------------------
# KPIs
# ----------------------------------------------------------------
def kpi_summary(dff):
    total = len(dff)
    avg_year = int(dff["release_year"].mean()) if total > 0 else 0
    top_country = dff["country_list"].mode().iloc[0] if total > 0 else "N/A"

    return pn.pane.Markdown(
        f"""
### 📊 Key Metrics
- **Total Titles:** {total:,}
- **Average Release Year:** {avg_year}
- **Most Common Country:** {top_country}
"""
    )

kpi_panel = pn.bind(kpi_summary, filtered)

# ----------------------------------------------------------------
# Plots
# ----------------------------------------------------------------
def year_plot(dff):
    if len(dff) == 0:
        return pn.pane.Markdown("_No data for selected filters._")
    df_year = dff.groupby("release_year").size().reset_index(name="Count")
    return df_year.hvplot.bar(
        x="release_year",
        y="Count",
        title="Titles by Release Year",
        xlabel="Year",
        ylabel="Count",
        color=ACCENT,
        height=350
    )

def type_plot(dff):
    if len(dff) == 0:
        return pn.pane.Markdown("_No data for selected filters._")
    counts = dff["type"].value_counts().reset_index()
    counts.columns = ["Type", "Count"]
    return counts.hvplot.bar(
        x="Type",
        y="Count",
        title="Content Type Distribution",
        xlabel="Type",
        ylabel="Count",
        color=ACCENT,
        height=350
    )

plots = pn.Row(
    pn.panel(pn.bind(year_plot, filtered), sizing_mode="stretch_both"),
    pn.panel(pn.bind(type_plot, filtered), sizing_mode="stretch_both"),
)

# ----------------------------------------------------------------
# Data Table
# ----------------------------------------------------------------
table = pn.widgets.Tabulator(filtered, pagination="remote", page_size=10, height=400)

# ----------------------------------------------------------------
# Dashboard Layout
# ----------------------------------------------------------------
dashboard = pn.template.FastListTemplate(
    title="🎬 Netflix Titles Dashboard",
    sidebar=[
        pn.pane.Markdown("### Filters"),
        type_select,
        country_select,
        year_slider,
    ],
    main=[
        pn.pane.Markdown("## Overview"),
        kpi_panel,
        plots,
        pn.pane.Markdown("## Data Table"),
        table,
    ],
    accent=ACCENT,
)

dashboard.servable()

