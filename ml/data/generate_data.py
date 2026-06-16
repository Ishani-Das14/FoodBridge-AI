"""
FoodBridge AI — Synthetic Donation Data Generator
Generates 10,000 realistic donation records for ML training.
"""

import os
import numpy as np
import pandas as pd

# ─── Reproducibility ──────────────────────────────────────────────────────────
SEED = 42
rng = np.random.default_rng(SEED)
N = 10_000

print("=" * 55)
print("  FoodBridge AI — Synthetic Data Generator")
print(f"  Generating {N:,} donation records …")
print("=" * 55)

# ─── 1. food_type ─────────────────────────────────────────────────────────────
FOOD_TYPES   = ["Rice", "Biryani", "Roti", "Dal", "Mixed", "Bread", "Curry"]
FOOD_WEIGHTS = [0.22,    0.18,     0.20,   0.12,  0.10,    0.08,    0.10]   # sum = 1.0

food_type = rng.choice(FOOD_TYPES, size=N, p=FOOD_WEIGHTS)

# ─── 2. quantity (packs) ──────────────────────────────────────────────────────
quantity = rng.normal(loc=35, scale=15, size=N)
quantity = np.clip(quantity, 5, 100).astype(int)

# ─── 3. prep_time_hour ────────────────────────────────────────────────────────
# Breakfast peak: 6–10 h  |  Dinner peak: 18–22 h
PREP_HOURS = [6, 7, 8, 9, 10, 18, 19, 20, 21, 22]
prep_time_hour = rng.choice(PREP_HOURS, size=N)

# ─── 4. expiry_minutes  (food-type dependent ± 20 % noise) ───────────────────
BASE_EXPIRY = {
    "Rice": 120, "Biryani": 150, "Roti": 90,
    "Dal": 180, "Mixed": 120, "Bread": 240, "Curry": 150,
}
base = np.array([BASE_EXPIRY[ft] for ft in food_type], dtype=float)
noise_factor = rng.uniform(0.80, 1.20, size=N)
expiry_minutes = (base * noise_factor).astype(int)

# ─── 5. distance_km ───────────────────────────────────────────────────────────
distance_km = rng.exponential(scale=5.0, size=N)
distance_km = np.clip(distance_km, 0.5, 25.0).round(2)

# ─── 6. weather_temp (°C) ─────────────────────────────────────────────────────
weather_temp = rng.normal(loc=30, scale=6, size=N)
weather_temp = np.clip(weather_temp, 15, 45).round(1)

# ─── 7. ngo_capacity (meals/day) ──────────────────────────────────────────────
NGO_CAPS = [20, 30, 40, 50, 60, 75, 100]
ngo_capacity = rng.choice(NGO_CAPS, size=N)

# ─── 8. traffic_factor ────────────────────────────────────────────────────────
traffic_factor = rng.uniform(0.8, 2.5, size=N).round(3)

# ─── 9. Label: delivered_on_time ──────────────────────────────────────────────
travel_time  = (distance_km / 30) * 60 * traffic_factor   # minutes
temp_penalty = np.maximum(0, (weather_temp - 35) * 2)
safe         = (expiry_minutes - travel_time - temp_penalty) > 15
delivered_on_time = safe.astype(int)

# Apply 8 % random label noise
flip_mask = rng.random(size=N) < 0.08
delivered_on_time[flip_mask] = 1 - delivered_on_time[flip_mask]

# ─── Assemble DataFrame ───────────────────────────────────────────────────────
df = pd.DataFrame({
    "food_type":        food_type,
    "quantity":         quantity,
    "prep_time_hour":   prep_time_hour,
    "expiry_minutes":   expiry_minutes,
    "distance_km":      distance_km,
    "weather_temp":     weather_temp,
    "ngo_capacity":     ngo_capacity,
    "traffic_factor":   traffic_factor,
    "delivered_on_time": delivered_on_time,
})

# ─── Save ─────────────────────────────────────────────────────────────────────
OUT_DIR  = os.path.dirname(__file__)
OUT_PATH = os.path.join(OUT_DIR, "synthetic_donations.csv")
df.to_csv(OUT_PATH, index=False)

# ─── Report ───────────────────────────────────────────────────────────────────
print(f"\n[OK] Saved -> {OUT_PATH}")
print(f"    Shape  : {df.shape[0]:,} rows x {df.shape[1]} columns\n")

vc = df["delivered_on_time"].value_counts().sort_index()
total = len(df)
print("  Target class distribution:")
print(f"    Not delivered on time  (0) : {vc[0]:5,}  ({vc[0]/total*100:.1f} %)")
print(f"    Delivered on time      (1) : {vc[1]:5,}  ({vc[1]/total*100:.1f} %)")

print("\n  Food-type breakdown:")
ft_stats = (df.groupby("food_type")["delivered_on_time"]
              .agg(count="count", success_rate="mean")
              .sort_values("success_rate"))
print(ft_stats.to_string())
print("\n  Numeric summary:")
print(df.describe().round(2).to_string())
print("\n  Done!")
