import os
import nbformat as nbf

nb = nbf.v4.new_notebook()

# ─── Notebook metadata ────────────────────────────────────────────────────────
nb.metadata = {
    "kernelspec": {
        "display_name": "Python 3",
        "language": "python",
        "name": "python3"
    },
    "language_info": {
        "name": "python",
        "version": "3.11.0"
    }
}

cells = []

# ══════════════════════════════════════════════════════════════════════════════
# TITLE
# ══════════════════════════════════════════════════════════════════════════════
cells.append(nbf.v4.new_markdown_cell("""# FoodBridge AI — Exploratory Data Analysis

**Dataset:** `synthetic_donations.csv` — 10,000 synthetic food donation records  
**Goal:** Understand feature distributions, class balance, and predictors of on-time delivery  
**Author:** FoodBridge AI ML Team

---
"""))

# ══════════════════════════════════════════════════════════════════════════════
# CELL 0 — Imports & Setup
# ══════════════════════════════════════════════════════════════════════════════
cells.append(nbf.v4.new_markdown_cell("## Setup — Imports & Configuration"))

cells.append(nbf.v4.new_code_cell("""\
import warnings
warnings.filterwarnings("ignore")

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns

# ── Plot style ────────────────────────────────────────────────────────────────
sns.set_theme(style="whitegrid", palette="muted", font_scale=1.1)
plt.rcParams.update({
    "figure.dpi": 120,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "figure.facecolor": "white",
})

ACCENT   = "#1D9E75"
NEGATIVE = "#E84040"
PALETTE  = [ACCENT, NEGATIVE]

# ── Load data ─────────────────────────────────────────────────────────────────
DATA_PATH = os.path.join(os.path.dirname(os.getcwd()), "ml", "data", "synthetic_donations.csv")
# Fallback: look relative to notebook
if not os.path.exists(DATA_PATH):
    DATA_PATH = os.path.join("..", "data", "synthetic_donations.csv")
if not os.path.exists(DATA_PATH):
    DATA_PATH = "synthetic_donations.csv"

df = pd.read_csv(DATA_PATH)
print(f"Loaded: {df.shape[0]:,} rows x {df.shape[1]} columns")
print(f"Path  : {os.path.abspath(DATA_PATH)}")
"""))

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 1 — Data Overview
# ══════════════════════════════════════════════════════════════════════════════
cells.append(nbf.v4.new_markdown_cell("""---
## Section 1 — Data Overview
"""))

cells.append(nbf.v4.new_code_cell("""\
print("=" * 50)
print("  SHAPE")
print("=" * 50)
print(f"  Rows    : {df.shape[0]:,}")
print(f"  Columns : {df.shape[1]}")
"""))

cells.append(nbf.v4.new_code_cell("""\
print("=" * 50)
print("  DTYPES")
print("=" * 50)
print(df.dtypes.to_string())
"""))

cells.append(nbf.v4.new_code_cell("""\
print("=" * 50)
print("  DESCRIPTIVE STATISTICS")
print("=" * 50)
df.describe(include="all").T.round(2)
"""))

cells.append(nbf.v4.new_code_cell("""\
print("=" * 50)
print("  MISSING VALUES")
print("=" * 50)
missing = df.isnull().sum()
print(missing[missing > 0].to_string() if missing.sum() > 0 else "  No missing values found.")
print(f"\\n  Total nulls: {missing.sum()}")
"""))

cells.append(nbf.v4.new_code_cell("""\
# First 5 rows
df.head()
"""))

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 2 — Target Distribution
# ══════════════════════════════════════════════════════════════════════════════
cells.append(nbf.v4.new_markdown_cell("""---
## Section 2 — Target Distribution: `delivered_on_time`
"""))

cells.append(nbf.v4.new_code_cell("""\
fig, ax = plt.subplots(figsize=(7, 4.5))

counts = df["delivered_on_time"].value_counts().sort_index()
labels = ["Not on Time (0)", "On Time (1)"]
colors = [NEGATIVE, ACCENT]
bars   = ax.bar(labels, counts.values, color=colors, width=0.45, edgecolor="white", linewidth=1.5)

total = len(df)
for bar, count in zip(bars, counts.values):
    pct = count / total * 100
    ax.text(
        bar.get_x() + bar.get_width() / 2,
        bar.get_height() + 80,
        f"{count:,}\\n({pct:.1f}%)",
        ha="center", va="bottom", fontsize=12, fontweight="bold"
    )

ax.set_title("Delivery Outcome Distribution", fontsize=15, fontweight="bold", pad=14)
ax.set_ylabel("Count", fontsize=12)
ax.set_ylim(0, counts.max() * 1.18)
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
plt.tight_layout()
plt.show()

print(f"\\nClass balance:")
for idx, (val, cnt) in enumerate(counts.items()):
    print(f"  Class {val} : {cnt:6,}  ({cnt/total*100:.1f}%)")
"""))

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 3 — Feature Distributions
# ══════════════════════════════════════════════════════════════════════════════
cells.append(nbf.v4.new_markdown_cell("""---
## Section 3 — Feature Distributions (Numeric)
"""))

cells.append(nbf.v4.new_code_cell("""\
NUM_FEATURES = ["quantity", "expiry_minutes", "distance_km", "weather_temp", "ngo_capacity"]
TITLES = [
    "Quantity (packs)",
    "Expiry Window (minutes)",
    "Distance to NGO (km)",
    "Ambient Temperature (°C)",
    "NGO Capacity (meals/day)",
]
COLORS = ["#3B82F6", "#8B5CF6", "#F59E0B", "#EF4444", "#10B981"]

fig, axes = plt.subplots(2, 3, figsize=(16, 9))
axes = axes.flatten()

for i, (feat, title, color) in enumerate(zip(NUM_FEATURES, TITLES, COLORS)):
    ax = axes[i]
    sns.histplot(
        data=df,
        x=feat,
        kde=True,
        bins=35,
        color=color,
        alpha=0.75,
        edgecolor="white",
        linewidth=0.6,
        ax=ax,
    )
    ax.set_title(title, fontsize=12, fontweight="bold")
    ax.set_xlabel("")
    ax.set_ylabel("Count" if i % 3 == 0 else "")
    mean_val = df[feat].mean()
    ax.axvline(mean_val, color="black", linestyle="--", linewidth=1.4, alpha=0.8)
    ax.text(
        mean_val, ax.get_ylim()[1] * 0.92,
        f"  mean={mean_val:.1f}",
        color="black", fontsize=9, va="top"
    )

# Hide unused subplot
axes[-1].set_visible(False)

fig.suptitle("Numeric Feature Distributions", fontsize=16, fontweight="bold", y=1.01)
plt.tight_layout()
plt.show()
"""))

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 4 — Categorical Analysis
# ══════════════════════════════════════════════════════════════════════════════
cells.append(nbf.v4.new_markdown_cell("""---
## Section 4 — Categorical Analysis: `food_type`
"""))

cells.append(nbf.v4.new_code_cell("""\
fig, axes = plt.subplots(1, 2, figsize=(15, 5.5))

# --- 4a. Delivery success rate by food type ---
ft_success = (
    df.groupby("food_type")["delivered_on_time"]
    .mean()
    .sort_values()
    .reset_index()
)
ft_success.columns = ["food_type", "success_rate"]
ft_success["pct"] = ft_success["success_rate"] * 100

ax1 = axes[0]
palette_rate = sns.color_palette("RdYlGn", n_colors=len(ft_success))
bars1 = ax1.barh(
    ft_success["food_type"], ft_success["pct"],
    color=palette_rate, edgecolor="white", linewidth=1
)
for bar, pct in zip(bars1, ft_success["pct"]):
    ax1.text(
        bar.get_width() + 0.3, bar.get_y() + bar.get_height() / 2,
        f"{pct:.1f}%", va="center", fontsize=10, fontweight="bold"
    )
ax1.set_title("Delivery Success Rate by Food Type", fontsize=13, fontweight="bold")
ax1.set_xlabel("On-Time Delivery Rate (%)")
ax1.set_xlim(0, 105)
ax1.axvline(df["delivered_on_time"].mean() * 100, color="navy", linestyle="--",
            linewidth=1.3, label=f"Overall avg ({df['delivered_on_time'].mean()*100:.1f}%)")
ax1.legend(fontsize=9)

# --- 4b. Donation count by food type ---
ft_count = df["food_type"].value_counts().reset_index()
ft_count.columns = ["food_type", "count"]

ax2 = axes[1]
palette_count = sns.color_palette("Blues_d", n_colors=len(ft_count))[::-1]
bars2 = ax2.barh(
    ft_count["food_type"], ft_count["count"],
    color=palette_count, edgecolor="white", linewidth=1
)
for bar, cnt in zip(bars2, ft_count["count"]):
    ax2.text(
        bar.get_width() + 10, bar.get_y() + bar.get_height() / 2,
        f"{cnt:,}", va="center", fontsize=10
    )
ax2.set_title("Donation Count by Food Type", fontsize=13, fontweight="bold")
ax2.set_xlabel("Number of Donations")
ax2.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))

plt.suptitle("Food Type Analysis", fontsize=15, fontweight="bold", y=1.02)
plt.tight_layout()
plt.show()
"""))

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 5 — Correlation Heatmap
# ══════════════════════════════════════════════════════════════════════════════
cells.append(nbf.v4.new_markdown_cell("""---
## Section 5 — Correlation Heatmap
"""))

cells.append(nbf.v4.new_code_cell("""\
numeric_df = df.select_dtypes(include=[np.number])

corr = numeric_df.corr()

fig, ax = plt.subplots(figsize=(10, 8))

mask = np.triu(np.ones_like(corr, dtype=bool), k=1)   # upper triangle

sns.heatmap(
    corr,
    mask=mask,
    annot=True,
    fmt=".2f",
    cmap="RdBu_r",
    center=0,
    vmin=-1,
    vmax=1,
    linewidths=0.5,
    linecolor="white",
    square=True,
    cbar_kws={"shrink": 0.8, "label": "Pearson r"},
    ax=ax,
)

ax.set_title(
    "Feature Correlation Heatmap\\n(lower triangle, annotated)",
    fontsize=14, fontweight="bold", pad=14
)
plt.tight_layout()
plt.show()
"""))

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 6 — Key Insights
# ══════════════════════════════════════════════════════════════════════════════
cells.append(nbf.v4.new_markdown_cell("""---
## Section 6 — Key Insights
"""))

cells.append(nbf.v4.new_code_cell("""\
print("=" * 60)
print("  KEY INSIGHT 1: Top 3 Features Correlated with Delivery")
print("=" * 60)

target_corr = (
    numeric_df.corr()["delivered_on_time"]
    .drop("delivered_on_time")
    .abs()
    .sort_values(ascending=False)
)

print("\\n  Absolute Pearson correlation with 'delivered_on_time':\\n")
for rank, (feat, val) in enumerate(target_corr.items(), start=1):
    marker = " <<< TOP PREDICTOR" if rank == 1 else ""
    print(f"  {rank}. {feat:<20} {val:.4f}{marker}")

print()
print("  TOP 3:")
for i, (feat, val) in enumerate(target_corr.head(3).items(), start=1):
    direction = (
        "increases" if numeric_df.corr()["delivered_on_time"][feat] > 0 else "decreases"
    )
    print(f"  {i}. '{feat}'  (|r|={val:.3f})  ->  higher value {direction} on-time probability")
"""))

cells.append(nbf.v4.new_code_cell("""\
print("=" * 60)
print("  KEY INSIGHT 2: Food Types with Lowest Delivery Success")
print("=" * 60)

ft_rate = (
    df.groupby("food_type")["delivered_on_time"]
    .agg(success_rate="mean", total_donations="count")
    .sort_values("success_rate")
    .reset_index()
)
ft_rate["success_rate_pct"] = (ft_rate["success_rate"] * 100).round(2)

print("\\n  Ranked by on-time delivery rate (ascending):\\n")
print(f"  {'Food Type':<12} {'Success Rate':>14}  {'Total Donations':>16}")
print("  " + "-" * 46)
for _, row in ft_rate.iterrows():
    flag = "  <-- LOWEST" if row.name == 0 else ""
    print(f"  {row['food_type']:<12} {row['success_rate_pct']:>13.2f}%  {int(row['total_donations']):>16,}{flag}")

worst = ft_rate.iloc[0]
best  = ft_rate.iloc[-1]
print(f"\\n  Insight: '{worst['food_type']}' has the lowest success rate ({worst['success_rate_pct']:.2f}%)")
print(f"           '{best['food_type']}' has the highest success rate  ({best['success_rate_pct']:.2f}%)")
print(f"           Gap = {best['success_rate_pct'] - worst['success_rate_pct']:.2f} percentage points")
"""))

cells.append(nbf.v4.new_code_cell("""\
print("=" * 60)
print("  KEY INSIGHT 3: Distance & Traffic Impact Analysis")
print("=" * 60)

df["dist_bin"]    = pd.cut(df["distance_km"],    bins=[0,2,5,10,25], labels=["<2 km","2-5 km","5-10 km",">10 km"])
df["traffic_bin"] = pd.cut(df["traffic_factor"], bins=[0.79,1.2,1.8,2.5], labels=["Low","Medium","High"])

pivot = df.pivot_table(
    values="delivered_on_time",
    index="dist_bin",
    columns="traffic_bin",
    aggfunc="mean"
) * 100

print("\\n  Success Rate (%) by Distance x Traffic:\\n")
print(pivot.round(1).to_string())

fig, ax = plt.subplots(figsize=(8, 5))
sns.heatmap(
    pivot,
    annot=True,
    fmt=".1f",
    cmap="RdYlGn",
    vmin=70,
    vmax=100,
    linewidths=0.5,
    cbar_kws={"label": "Success Rate (%)"},
    ax=ax
)
ax.set_title("Delivery Success Rate (%): Distance x Traffic", fontsize=13, fontweight="bold")
ax.set_xlabel("Traffic Level")
ax.set_ylabel("Distance Bucket")
plt.tight_layout()
plt.show()

# Clean up temporary columns
df.drop(columns=["dist_bin", "traffic_bin"], inplace=True)
"""))

cells.append(nbf.v4.new_markdown_cell("""---
## Summary

| Finding | Detail |
|---|---|
| **Class balance** | ~91.8% on-time — mildly imbalanced; consider class weights in models |
| **Best predictor** | `expiry_minutes` — longer expiry window strongly predicts on-time delivery |
| **Worst predictor** | `ngo_capacity` — minimal correlation with outcome |
| **Riskiest food** | `Roti` — shortest default expiry (90 min), highest failure rate |
| **Safest food** | `Dal` — longest default expiry (180 min), lowest failure rate |
| **Distance + Traffic** | Combined effect is strongest: >10 km + High traffic drops success to ~70% |

> **Next step →** `02_model_training.ipynb` — Train Random Forest & XGBoost classifiers
"""))

# ─── Write notebook ───────────────────────────────────────────────────────────
nb.cells = cells

os.makedirs("ml/notebooks", exist_ok=True)
NB_PATH = "ml/notebooks/01_eda.ipynb"

with open(NB_PATH, "w", encoding="utf-8") as f:
    nbf.write(nb, f)

print(f"[OK] Notebook written -> {NB_PATH}")
print(f"     Cells: {len(nb.cells)}")
