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
cells.append(nbf.v4.new_markdown_cell("""# FoodBridge AI — Feature Engineering

**Dataset:** `synthetic_donations.csv`
**Goal:** Apply the `FeatureEngineer` class to the raw data and inspect the resulting feature matrix.
**Author:** FoodBridge AI ML Team

---
"""))

# ══════════════════════════════════════════════════════════════════════════════
# CELL 0 — Imports & Setup
# ══════════════════════════════════════════════════════════════════════════════
cells.append(nbf.v4.new_code_cell("""\
import os
import sys
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Add the project root to sys.path so we can import ml.features.engineering
sys.path.append(os.path.abspath(os.path.join(os.getcwd(), '..', '..')))

from ml.features.engineering import FeatureEngineer

# Plot styling
sns.set_theme(style="whitegrid", palette="muted")
plt.rcParams.update({
    "figure.dpi": 120,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "figure.facecolor": "white",
})
"""))

# ══════════════════════════════════════════════════════════════════════════════
# CELL 1 — Load Data
# ══════════════════════════════════════════════════════════════════════════════
cells.append(nbf.v4.new_markdown_cell("""## 1. Load Raw Data"""))

cells.append(nbf.v4.new_code_cell("""\
DATA_PATH = os.path.join(os.path.abspath(os.path.join(os.getcwd(), '..', 'data')), "synthetic_donations.csv")

# Fallback for different working directories
if not os.path.exists(DATA_PATH):
    DATA_PATH = os.path.join("..", "data", "synthetic_donations.csv")

df_raw = pd.read_csv(DATA_PATH)
print(f"Loaded raw data: {df_raw.shape[0]:,} rows x {df_raw.shape[1]} columns")
df_raw.head()
"""))

# ══════════════════════════════════════════════════════════════════════════════
# CELL 2 — Apply FeatureEngineer
# ══════════════════════════════════════════════════════════════════════════════
cells.append(nbf.v4.new_markdown_cell("""## 2. Apply Feature Engineering pipeline"""))

cells.append(nbf.v4.new_code_cell("""\
fe = FeatureEngineer()
df_transformed, feature_names = fe.transform(df_raw)

print("=" * 50)
print("  SHAPE COMPARISON")
print("=" * 50)
print(f"  Shape before : {df_raw.shape}")
print(f"  Shape after  : {df_transformed.shape}")

print("\\n=" * 50)
print("  FEATURE NAMES")
print("=" * 50)
print(f"Total features: {len(feature_names)}")
for f in feature_names:
    print(f"  - {f}")
"""))

# ══════════════════════════════════════════════════════════════════════════════
# CELL 3 — Inspect Transformed Data
# ══════════════════════════════════════════════════════════════════════════════
cells.append(nbf.v4.new_markdown_cell("""## 3. Inspect Transformed Matrix"""))

cells.append(nbf.v4.new_code_cell("""\
# Show first 5 rows of transformed features
df_transformed.head()
"""))

# ══════════════════════════════════════════════════════════════════════════════
# CELL 4 — Feature Importance Proxy
# ══════════════════════════════════════════════════════════════════════════════
cells.append(nbf.v4.new_markdown_cell("""## 4. Feature Importance Proxy (Correlation with Label)

We check how each newly engineered feature correlates with our target label `delivered_on_time`.
"""))

cells.append(nbf.v4.new_code_cell("""\
# Calculate correlation of all features with the label
correlations = df_transformed.corr()["delivered_on_time"].drop("delivered_on_time").sort_values()

# Plot
fig, ax = plt.subplots(figsize=(10, 8))
colors = ["#E84040" if c < 0 else "#1D9E75" for c in correlations]
correlations.plot(kind="barh", color=colors, ax=ax)

ax.set_title("Feature Correlation with 'delivered_on_time'", fontsize=14, fontweight="bold", pad=15)
ax.set_xlabel("Pearson Correlation Coefficient")
ax.set_ylabel("Feature")
ax.axvline(0, color="black", linewidth=1.2)

# Annotate values
for idx, val in enumerate(correlations):
    offset = 0.01 if val > 0 else -0.01
    ha = "left" if val > 0 else "right"
    ax.text(val + offset, idx, f"{val:.3f}", va="center", ha=ha, fontsize=10)

# Expand x-limits slightly to make room for annotations
xmin, xmax = ax.get_xlim()
limit = max(abs(xmin), abs(xmax)) * 1.15
ax.set_xlim(-limit, limit)

plt.tight_layout()
plt.show()
"""))


# ─── Write notebook ───────────────────────────────────────────────────────────
nb.cells = cells

os.makedirs("ml/notebooks", exist_ok=True)
NB_PATH = "ml/notebooks/02_features.ipynb"

with open(NB_PATH, "w", encoding="utf-8") as f:
    nbf.write(nb, f)

print(f"[OK] Notebook written -> {NB_PATH}")
print(f"     Cells: {len(nb.cells)}")
