import os
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import joblib
from sklearn.preprocessing import MinMaxScaler

class LSTMNet(nn.Module):
    def __init__(self, input_size=1, hidden_size=64, num_layers=2):
        super(LSTMNet, self).__init__()
        self.lstm = nn.LSTM(input_size=input_size, hidden_size=hidden_size, 
                            num_layers=num_layers, batch_first=True)
        self.linear = nn.Linear(hidden_size, 1)

    def forward(self, x):
        lstm_out, _ = self.lstm(x)
        # Take the output of the last time step
        last_out = lstm_out[:, -1, :]
        out = self.linear(last_out)
        return out

class LSTMForecaster:
    def __init__(self, model_dir=None):
        if model_dir is None:
            self.model_dir = os.path.dirname(__file__)
        else:
            self.model_dir = model_dir
        os.makedirs(self.model_dir, exist_ok=True)
        
    def _get_model_path(self, ngo_id: str) -> str:
        return os.path.join(self.model_dir, f"lstm_{ngo_id}.pt")

    def _get_scaler_path(self, ngo_id: str) -> str:
        return os.path.join(self.model_dir, f"scaler_{ngo_id}.pkl")

    def prepare_sequences(self, series: np.ndarray, lookback: int = 7):
        X, y = [], []
        for i in range(len(series) - lookback):
            X.append(series[i:(i + lookback)])
            y.append(series[i + lookback])
        return np.array(X), np.array(y)

    def train(self, ngo_id: str, series: np.ndarray, epochs: int = 50, lookback: int = 7):
        """
        Trains an LSTM model for a specific NGO.
        series: 1D numpy array of historical daily demand
        """
        # Normalize
        scaler = MinMaxScaler(feature_range=(0, 1))
        series_scaled = scaler.fit_transform(series.reshape(-1, 1))
        
        # Prepare sequences
        X, y = self.prepare_sequences(series_scaled, lookback)
        
        # Convert to PyTorch tensors
        # X shape: (batch, seq_len, features) -> (N, lookback, 1)
        X_tensor = torch.tensor(X, dtype=torch.float32)
        y_tensor = torch.tensor(y, dtype=torch.float32).view(-1, 1)
        
        model = LSTMNet(input_size=1, hidden_size=64, num_layers=2)
        criterion = nn.MSELoss()
        optimizer = optim.Adam(model.parameters(), lr=0.01)
        
        # Train
        model.train()
        for epoch in range(1, epochs + 1):
            optimizer.zero_grad()
            out = model(X_tensor)
            loss = criterion(out, y_tensor)
            loss.backward()
            optimizer.step()
            
            if epoch % 10 == 0:
                print(f"NGO {ngo_id} - Epoch {epoch}/{epochs}, Loss: {loss.item():.6f}")
                
        # Save model and scaler
        torch.save(model.state_dict(), self._get_model_path(ngo_id))
        joblib.dump(scaler, self._get_scaler_path(ngo_id))
        print(f"LSTM model saved for NGO {ngo_id}")
        return model

    def predict(self, ngo_id: str, recent_7_days: list) -> float:
        """
        Predicts tomorrow's demand based on the last 7 days of actual demand.
        """
        model_path = self._get_model_path(ngo_id)
        scaler_path = self._get_scaler_path(ngo_id)
        
        if not os.path.exists(model_path) or not os.path.exists(scaler_path):
            raise FileNotFoundError(f"No trained LSTM model/scaler found for NGO {ngo_id}")
            
        scaler = joblib.load(scaler_path)
        model = LSTMNet(input_size=1, hidden_size=64, num_layers=2)
        model.load_state_dict(torch.load(model_path))
        model.eval()
        
        # Preprocess input
        recent_arr = np.array(recent_7_days).reshape(-1, 1)
        recent_scaled = scaler.transform(recent_arr)
        
        # Shape: (1, 7, 1)
        X_tensor = torch.tensor(recent_scaled, dtype=torch.float32).unsqueeze(0)
        
        with torch.no_grad():
            out_scaled = model(X_tensor)
            
        out_scaled_np = out_scaled.numpy().reshape(-1, 1)
        pred_value = scaler.inverse_transform(out_scaled_np)[0][0]
        
        return max(0.0, float(pred_value))
