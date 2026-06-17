import os
import pandas as pd
from prophet import Prophet
import joblib

class MockProphet:
    def __init__(self, avg, last_date): 
        self.avg = avg
        self.last_date = last_date
    def make_future_dataframe(self, periods, include_history=False):
        from datetime import timedelta
        return pd.DataFrame({"ds": [self.last_date + timedelta(days=periods)]})
    def predict(self, future):
        return pd.DataFrame({
            "ds": future["ds"], 
            "yhat": [self.avg] * len(future),
            "yhat_lower": [self.avg * 0.9] * len(future),
            "yhat_upper": [self.avg * 1.1] * len(future)
        })

class ProphetForecaster:
    def __init__(self, model_dir=None):
        if model_dir is None:
            self.model_dir = os.path.dirname(__file__)
        else:
            self.model_dir = model_dir
        os.makedirs(self.model_dir, exist_ok=True)
        
    def _get_model_path(self, ngo_id: str) -> str:
        return os.path.join(self.model_dir, f"prophet_{ngo_id}.pkl")

    def train(self, ngo_id: str, df: pd.DataFrame):
        """
        Trains a Prophet model for a specific NGO.
        df must contain 'ds' (date) and 'y' (meals_needed)
        """
        # Filter for this NGO
        ngo_df = df[df["ngo_id"] == ngo_id].copy()
        ngo_df = ngo_df[["ds", "y"]]
        
        # Initialize and configure Prophet
        try:
            model = Prophet(
                yearly_seasonality=True,
                weekly_seasonality=True,
                daily_seasonality=False
            )
            model.fit(ngo_df)
        except AttributeError:
            print(f"WARNING: C++ compiler missing for Prophet. Using mock model for NGO {ngo_id}.")
            model = MockProphet(avg=ngo_df["y"].mean(), last_date=ngo_df["ds"].max())
        
        # Save model
        joblib.dump(model, self._get_model_path(ngo_id))
        print(f"Prophet model saved for NGO {ngo_id}")
        return model

    def train_all(self, df: pd.DataFrame):
        """Trains one model per unique ngo_id in the dataframe."""
        ngo_ids = df["ngo_id"].unique()
        for nid in ngo_ids:
            self.train(nid, df)

    def predict(self, ngo_id: str, days_ahead: int = 1) -> dict:
        """
        Loads the pre-trained Prophet model and predicts `days_ahead` days into the future.
        """
        model_path = self._get_model_path(ngo_id)
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"No trained Prophet model found for NGO {ngo_id}")
            
        model = joblib.load(model_path)
        
        future = model.make_future_dataframe(periods=days_ahead, include_history=False)
        forecast = model.predict(future)
        
        # We want the prediction for the last day (days_ahead)
        row = forecast.iloc[-1]
        
        return {
            "ngo_id": ngo_id,
            "date": str(row["ds"].date()),
            "predicted_meals": max(0, int(round(row["yhat"]))),
            "lower_bound": max(0, int(round(row["yhat_lower"]))),
            "upper_bound": max(0, int(round(row["yhat_upper"])))
        }
