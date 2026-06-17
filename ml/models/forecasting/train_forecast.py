import os
import sys
import pandas as pd
import numpy as np

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.append(project_root)

from ml.models.forecasting.prophet_model import ProphetForecaster
from ml.models.forecasting.lstm_model import LSTMForecaster

DATA_DIR = os.path.join(project_root, "ml", "data")
OUT_CSV = os.path.join(DATA_DIR, "ngo_demand_timeseries.csv")

def generate_synthetic_timeseries():
    """Generates 180 days of daily food demand for 5 simulated NGOs."""
    print("Generating synthetic timeseries data...")
    os.makedirs(DATA_DIR, exist_ok=True)
    
    np.random.seed(42)
    ngo_bases = [40, 55, 30, 70, 45]
    ngo_ids = [str(i) for i in range(1, 6)]
    
    # 180 days ending today
    end_date = pd.Timestamp.now().normalize()
    dates = pd.date_range(end_date - pd.Timedelta(days=179), end_date)
    
    records = []
    for ngo_idx, ngo_id in enumerate(ngo_ids):
        base_demand = ngo_bases[ngo_idx]
        
        for d in dates:
            # Check if weekend (Saturday=5, Sunday=6)
            is_weekend = d.weekday() >= 5
            
            # Weekend multiplier (+20%)
            weekend_mult = 1.2 if is_weekend else 1.0
            
            # Random noise std=5
            noise = np.random.normal(0, 5)
            
            # Calculate final demand
            meals = max(0, int(round((base_demand * weekend_mult) + noise)))
            
            records.append({
                "ds": d,
                "ngo_id": ngo_id,
                "y": meals
            })
            
    df = pd.DataFrame(records)
    df.to_csv(OUT_CSV, index=False)
    print(f"Saved synthetic timeseries -> {OUT_CSV}")
    return df

def train_models(df):
    """Trains both Prophet and LSTM models."""
    print("\nTraining Prophet models...")
    prophet_fc = ProphetForecaster()
    prophet_fc.train_all(df)
    
    print("\nTraining LSTM models...")
    lstm_fc = LSTMForecaster()
    ngo_ids = df["ngo_id"].unique()
    for nid in ngo_ids:
        series = df[df["ngo_id"] == nid]["y"].values
        lstm_fc.train(nid, series, epochs=50)

if __name__ == "__main__":
    df = generate_synthetic_timeseries()
    train_models(df)
    print("\nDone training all forecasting models!")
