"""
FoodBridge AI — Feature Engineering Module
==========================================
Transforms raw donation records into a clean, ML-ready feature matrix.

Dependencies: pandas, numpy only (no sklearn)
"""

import numpy as np
import pandas as pd
from typing import List, Tuple


# ──────────────────────────────────────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────────────────────────────────────

PERISHABILITY_MAP = {
    "Rice":    0.80,
    "Biryani": 0.70,
    "Roti":    0.90,
    "Dal":     0.50,
    "Mixed":   0.75,
    "Bread":   0.30,
    "Curry":   0.65,
}

DISTANCE_BINS = [
    (3.0,  "very_near"),
    (7.0,  "near"),
    (15.0, "moderate"),
    (float("inf"), "far"),
]

PEAK_HOURS_BREAKFAST = range(7, 10)   # 7, 8, 9
PEAK_HOURS_DINNER    = range(19, 23)  # 19, 20, 21, 22

AVG_SPEED_KMH = 30.0   # assumed urban delivery speed


# ──────────────────────────────────────────────────────────────────────────────
# FeatureEngineer
# ──────────────────────────────────────────────────────────────────────────────

class FeatureEngineer:
    """
    Transforms raw FoodBridge donation records into an ML-ready feature matrix.

    All row-level transforms are deterministic and stateless; only the
    :meth:`transform` pipeline mutates the dataframe (returns a copy).

    Usage
    -----
    >>> fe = FeatureEngineer()
    >>> X, feature_names = fe.transform(raw_df)
    """

    # ── Row-level feature methods ─────────────────────────────────────────────

    @staticmethod
    def time_to_expiry(row: pd.Series) -> float:
        """
        Compute the remaining buffer time (minutes) after the food is delivered.

        Formula
        -------
        travel_time = (distance_km / 30) * 60 * traffic_factor
        buffer      = expiry_minutes - travel_time

        Parameters
        ----------
        row : pd.Series
            Must contain: expiry_minutes, distance_km, traffic_factor.

        Returns
        -------
        float
            Minutes of buffer remaining. Negative means the food will have
            expired before delivery.
        """
        distance_km    = float(row.get("distance_km", 0))
        traffic_factor = float(row.get("traffic_factor", 1.0))
        expiry_minutes = float(row.get("expiry_minutes", 0))

        travel_time = (distance_km / AVG_SPEED_KMH) * 60.0 * traffic_factor
        return expiry_minutes - travel_time

    @staticmethod
    def distance_bucket(distance_km: float) -> str:
        """
        Bin a continuous distance (km) into an ordinal category.

        Buckets
        -------
        - 0–3 km   → "very_near"
        - 3–7 km   → "near"
        - 7–15 km  → "moderate"
        - 15+ km   → "far"

        Parameters
        ----------
        distance_km : float
            Straight-line or road distance in kilometres.

        Returns
        -------
        str
            One of {"very_near", "near", "moderate", "far"}.
        """
        try:
            d = float(distance_km)
        except (TypeError, ValueError):
            return "very_near"   # safe default for missing/bad input

        for threshold, label in DISTANCE_BINS:
            if d < threshold:
                return label
        return "far"   # unreachable but explicit

    @staticmethod
    def food_perishability_score(food_type: str) -> float:
        """
        Return a normalised perishability score for a given food type.

        Higher score = spoils faster = higher delivery urgency.

        Scores
        ------
        Roti=0.9, Rice=0.8, Mixed=0.75, Biryani=0.7, Curry=0.65,
        Dal=0.5, Bread=0.3

        Parameters
        ----------
        food_type : str
            Name of the food item (case-sensitive).

        Returns
        -------
        float
            Score in [0.0, 1.0]. Unknown types return 0.7 (neutral default).
        """
        if not isinstance(food_type, str):
            return 0.70   # neutral default for NaN / non-string
        return PERISHABILITY_MAP.get(food_type.strip(), 0.70)

    @staticmethod
    def capacity_ratio(quantity: float, ngo_capacity: float) -> float:
        """
        Fraction of NGO daily capacity that this donation fills.

        Clipped to [0.0, 1.0]; values >1.0 indicate the donation exceeds
        the NGO's capacity for the day (treated as 1.0 = full utilisation).

        Parameters
        ----------
        quantity : float
            Number of meal packs in the donation.
        ngo_capacity : float
            NGO's maximum meals per day.

        Returns
        -------
        float
            Ratio in [0.0, 1.0]. Returns 0.0 if ngo_capacity <= 0 or NaN.
        """
        try:
            q  = float(quantity)
            nc = float(ngo_capacity)
        except (TypeError, ValueError):
            return 0.0

        if nc <= 0 or np.isnan(nc):
            return 0.0
        return float(np.clip(q / nc, 0.0, 1.0))

    @staticmethod
    def is_peak_hour(prep_time_hour: int) -> int:
        """
        Flag whether a donation was prepared during a peak meal hour.

        Peak windows
        ------------
        - Breakfast : 7, 8, 9
        - Dinner    : 19, 20, 21, 22

        Parameters
        ----------
        prep_time_hour : int
            Hour of preparation (0–23).

        Returns
        -------
        int
            1 if peak hour, 0 otherwise. Returns 0 for missing/invalid input.
        """
        try:
            h = int(prep_time_hour)
        except (TypeError, ValueError):
            return 0

        return int(h in PEAK_HOURS_BREAKFAST or h in PEAK_HOURS_DINNER)

    # ── Pipeline ──────────────────────────────────────────────────────────────

    def transform(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
        """
        Apply all feature transformations and return the ML-ready matrix.

        Steps
        -----
        1. Compute scalar engineered features (time_to_expiry, perishability,
           capacity_ratio, is_peak_hour).
        2. Compute distance_bucket category then one-hot encode it.
        3. One-hot encode food_type.
        4. Drop the raw distance_km and food_type columns.
        5. Fill any remaining NaNs with 0.

        Parameters
        ----------
        df : pd.DataFrame
            Raw donations dataframe. Expected columns:
            food_type, quantity, prep_time_hour, expiry_minutes,
            distance_km, weather_temp, ngo_capacity, traffic_factor.
            Optionally: delivered_on_time (label).

        Returns
        -------
        Tuple[pd.DataFrame, List[str]]
            - Transformed feature DataFrame (label excluded from feature names).
            - List of feature column names.

        Raises
        ------
        ValueError
            If none of the expected input columns are present.
        """
        required = {
            "food_type", "quantity", "prep_time_hour", "expiry_minutes",
            "distance_km", "weather_temp", "ngo_capacity", "traffic_factor",
        }
        present = set(df.columns)
        if not required.intersection(present):
            raise ValueError(
                f"DataFrame has none of the expected columns. "
                f"Expected at least one of: {required}"
            )

        out = df.copy()

        # ── 1. Scalar features ────────────────────────────────────────────────
        out["time_to_expiry"] = out.apply(self.time_to_expiry, axis=1)

        out["food_perishability_score"] = out["food_type"].map(
            lambda ft: self.food_perishability_score(ft)
        )

        out["capacity_ratio"] = out.apply(
            lambda r: self.capacity_ratio(
                r.get("quantity", 0), r.get("ngo_capacity", 1)
            ),
            axis=1,
        )

        out["is_peak_hour"] = out["prep_time_hour"].map(self.is_peak_hour)

        # ── 2. Distance bucket → one-hot ──────────────────────────────────────
        out["_dist_bucket"] = out["distance_km"].map(self.distance_bucket)
        dist_dummies = pd.get_dummies(
            out["_dist_bucket"], prefix="dist", dtype=int
        )
        # Ensure all bucket columns exist even if a category is absent
        for bucket in ["very_near", "near", "moderate", "far"]:
            col = f"dist_{bucket}"
            if col not in dist_dummies.columns:
                dist_dummies[col] = 0
        dist_dummies = dist_dummies[
            ["dist_very_near", "dist_near", "dist_moderate", "dist_far"]
        ]

        # ── 3. Food type → one-hot ────────────────────────────────────────────
        food_dummies = pd.get_dummies(
            out["food_type"].fillna("Unknown"), prefix="food", dtype=int
        )

        # ── 4. Drop raw columns no longer needed ──────────────────────────────
        out = out.drop(columns=["food_type", "distance_km", "_dist_bucket",
                                 "prep_time_hour"],
                       errors="ignore")

        # ── 5. Concatenate one-hot columns ────────────────────────────────────
        out = pd.concat([out, dist_dummies, food_dummies], axis=1)

        # ── 6. Fill residual NaNs ─────────────────────────────────────────────
        out = out.fillna(0)

        # ── Collect feature names (exclude label if present) ──────────────────
        label_col = "delivered_on_time"
        feature_names = [c for c in out.columns if c != label_col]

        return out, feature_names

    def get_feature_names(self, df: pd.DataFrame) -> List[str]:
        """
        Return the list of feature column names produced by :meth:`transform`.

        Parameters
        ----------
        df : pd.DataFrame
            A sample of the raw input DataFrame (does not need to be full dataset).

        Returns
        -------
        List[str]
            Ordered list of feature column names.
        """
        _, names = self.transform(df.head(5))
        return names


# ──────────────────────────────────────────────────────────────────────────────
# Quick smoke-test (run file directly)
# ──────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import os

    DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "synthetic_donations.csv")
    df = pd.read_csv(DATA_PATH)

    fe = FeatureEngineer()
    X, names = fe.transform(df)

    print("=" * 55)
    print("  FoodBridge AI - Feature Engineering Smoke Test")
    print("=" * 55)
    print(f"\n  Input  shape : {df.shape}")
    print(f"  Output shape : {X.shape}")
    print(f"\n  Features ({len(names)}):")
    for n in names:
        print(f"    - {n}")

    print("\n  Sample (first row):")
    print(X[names].head(1).T.to_string())
    print("\n  No errors. Feature engineering OK!")
