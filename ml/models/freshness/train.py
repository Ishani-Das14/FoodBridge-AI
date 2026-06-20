import os
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import joblib

from sklearn.model_selection import train_test_split, StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, confusion_matrix, f1_score, precision_score, recall_score, roc_auc_score
from xgboost import XGBClassifier

# Add project root to sys.path to import ml.features.engineering
import sys
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.append(project_root)

from ml.features.engineering import FeatureEngineer

# ─── Configuration ────────────────────────────────────────────────────────────
DATA_PATH = os.environ.get("TRAIN_DATA_PATH", os.path.join(project_root, "ml", "data", "synthetic_donations.csv"))
OUT_DIR = os.path.dirname(__file__)

MODEL_PATH = os.environ.get("MODEL_OUTPUT_PATH", os.path.join(OUT_DIR, "freshness_model.pkl"))
NAMES_PATH = os.path.join(OUT_DIR, "feature_names.json")
PLOT_PATH = os.path.join(OUT_DIR, "feature_importance.png")

# ─── Step 1 & 2: Load Data & Engineer Features ────────────────────────────────
print("Loading data...")
df_raw = pd.read_csv(DATA_PATH)

print("Engineering features...")
fe = FeatureEngineer()
df_transformed, feature_names = fe.transform(df_raw)

# Extract X and y
y = df_raw["delivered_on_time"].values
X = df_transformed[feature_names].values

# ─── Step 3: Train / Test Split ───────────────────────────────────────────────
print("Splitting data...")
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.20, stratify=y, random_state=42
)

print(f"  Train shape : {X_train.shape}")
print(f"  Test shape  : {X_test.shape}")

# ─── Step 4: Build Pipeline ───────────────────────────────────────────────────
pipeline = Pipeline([
    ("scaler", StandardScaler()),
    ("xgb", XGBClassifier(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.05,
        use_label_encoder=False,
        eval_metric='logloss',
        random_state=42
    ))
])

# ─── Step 5: 5-fold Stratified CV ─────────────────────────────────────────────
print("\nRunning 5-fold Stratified CV...")
skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

cv_metrics = {
    "f1": [], "precision": [], "recall": [], "roc_auc": []
}

for train_idx, val_idx in skf.split(X_train, y_train):
    X_fold_train, X_fold_val = X_train[train_idx], X_train[val_idx]
    y_fold_train, y_fold_val = y_train[train_idx], y_train[val_idx]
    
    pipeline.fit(X_fold_train, y_fold_train)
    y_pred = pipeline.predict(X_fold_val)
    y_proba = pipeline.predict_proba(X_fold_val)[:, 1]
    
    cv_metrics["f1"].append(f1_score(y_fold_val, y_pred))
    cv_metrics["precision"].append(precision_score(y_fold_val, y_pred))
    cv_metrics["recall"].append(recall_score(y_fold_val, y_pred))
    cv_metrics["roc_auc"].append(roc_auc_score(y_fold_val, y_proba))

print("Cross-Validation Results:")
for metric, scores in cv_metrics.items():
    print(f"  {metric.upper():<10}: {np.mean(scores):.4f} ± {np.std(scores):.4f}")

# ─── Step 6: Train Final Model ────────────────────────────────────────────────
print("\nTraining final model on full training set...")
pipeline.fit(X_train, y_train)

# ─── Step 7: Evaluate on Test Set ─────────────────────────────────────────────
print("\nEvaluating on test set...")
y_test_pred = pipeline.predict(X_test)
print("\nClassification Report:")
print(classification_report(y_test, y_test_pred))

print("Confusion Matrix:")
cm = confusion_matrix(y_test, y_test_pred)
print(cm)

# ─── Step 8: Plot Feature Importance ──────────────────────────────────────────
print("\nExtracting feature importances...")
# The XGBClassifier is the second step in the pipeline
xgb_model = pipeline.named_steps["xgb"]
importances = xgb_model.feature_importances_

# Sort top 15 features
indices = np.argsort(importances)[-15:]
top_features = [feature_names[i] for i in indices]
top_importances = importances[indices]

fig, ax = plt.subplots(figsize=(10, 6))
ax.barh(top_features, top_importances, color="#1D9E75", edgecolor="white")
ax.set_title("Top 15 Feature Importances (XGBoost)", fontsize=14, fontweight="bold")
ax.set_xlabel("Relative Importance")
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
plt.tight_layout()

plt.savefig(PLOT_PATH, dpi=120)
print(f"Saved feature importance plot -> {PLOT_PATH}")

# ─── Step 9 & 10: Save Model and Feature Names ────────────────────────────────
print("\nSaving model artifacts...")
joblib.dump(pipeline, MODEL_PATH)
print(f"  Model saved -> {MODEL_PATH}")

with open(NAMES_PATH, "w") as f:
    json.dump(feature_names, f, indent=4)
print(f"  Feature names saved -> {NAMES_PATH}")

print("\nDone!")
