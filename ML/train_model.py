# ml/train_model.py
import sqlite3
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from sklearn.preprocessing import StandardScaler
import pickle
from pathlib import Path

# --- Configuration ---
ROOT_DIR = Path(__file__).resolve().parent.parent
DB_PATH = ROOT_DIR / "data" / "health_data.db"
MODEL_DIR = ROOT_DIR / "ml" / "models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

# Select hardware accelerator
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f"🚀 Training on device: {device}")

# --- 1. Data Preparation ---
def load_and_prep_data():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT date, step_count, resting_hr, sleep_hours FROM daily_metrics ORDER BY date ASC", conn)
    conn.close()

    # Create the target variable: Tomorrow's Resting Heart Rate
    df['target_hr_tomorrow'] = df['resting_hr'].shift(-1)
    df = df.dropna() # Remove the last row since we don't know tomorrow yet

    features = df[['step_count', 'resting_hr', 'sleep_hours']].values
    targets = df[['target_hr_tomorrow']].values

    # Normalize the data (Crucial for Neural Networks)
    scaler_X = StandardScaler()
    scaler_y = StandardScaler()
    
    X_scaled = scaler_X.fit_transform(features)
    y_scaled = scaler_y.fit_transform(targets)

    # Save the scalers for inference later
    with open(MODEL_DIR / 'scaler_X.pkl', 'wb') as f:
        pickle.dump(scaler_X, f)
    with open(MODEL_DIR / 'scaler_y.pkl', 'wb') as f:
        pickle.dump(scaler_y, f)

    return torch.FloatTensor(X_scaled).to(device), torch.FloatTensor(y_scaled).to(device)

# --- 2. PyTorch Model Definition ---
class HealthPredictorNet(nn.Module):
    def __init__(self, input_size=3):
        super(HealthPredictorNet, self).__init__()
        self.network = nn.Sequential(
            nn.Linear(input_size, 16),
            nn.ReLU(),
            nn.Linear(16, 8),
            nn.ReLU(),
            nn.Linear(8, 1)
        )

    def forward(self, x):
        return self.network(x)

# --- 3. Training Loop ---
def train():
    X, y = load_and_prep_data()
    
    model = HealthPredictorNet().to(device)
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=0.01)

    epochs = 500
    for epoch in range(epochs):
        optimizer.zero_grad()
        predictions = model(X)
        loss = criterion(predictions, y)
        loss.backward()
        optimizer.step()

        if (epoch + 1) % 100 == 0:
            print(f"Epoch {epoch+1}/{epochs} | Loss: {loss.item():.4f}")

    # Save the trained weights
    torch.save(model.state_dict(), MODEL_DIR / "health_model.pth")
    print("✅ Model weights saved to health_model.pth")

if __name__ == "__main__":
    train()