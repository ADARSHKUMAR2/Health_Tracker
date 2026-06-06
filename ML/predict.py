# ml/predict.py
import sqlite3
import torch
import pickle
from pathlib import Path
from ML.train_model import HealthPredictorNet

ROOT_DIR = Path(__file__).resolve().parent.parent
DB_PATH = ROOT_DIR / "data" / "health_data.db"
MODEL_DIR = ROOT_DIR / "ml" / "models"

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

def get_tomorrows_hr_prediction() -> dict:
    """Fetches today's data and runs a forward pass through the PyTorch model."""
    try:
        # 1. Load the latest row of data from SQLite
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT step_count, resting_hr, sleep_hours FROM daily_metrics ORDER BY date DESC LIMIT 1")
        row = cursor.fetchone()
        conn.close()

        if not row:
            return {"error": "Not enough data to make a prediction."}

        # 2. Load the trained model and scalers
        model = HealthPredictorNet().to(device)
        model.load_state_dict(torch.load(MODEL_DIR / "health_model.pth", map_location=device, weights_only=True))
        model.eval()

        with open(MODEL_DIR / 'scaler_X.pkl', 'rb') as f:
            scaler_X = pickle.load(f)
        with open(MODEL_DIR / 'scaler_y.pkl', 'rb') as f:
            scaler_y = pickle.load(f)

        # 3. Run Inference
        today_features = scaler_X.transform([row])
        tensor_features = torch.FloatTensor(today_features).to(device)

        with torch.no_grad():
            scaled_prediction = model(tensor_features).cpu().numpy()

        # 4. Inverse transform to get actual BPM
        predicted_bpm = scaler_y.inverse_transform(scaled_prediction)[0][0]

        return {
            "prediction": "success",
            "predicted_resting_hr": round(float(predicted_bpm), 1),
            "based_on_steps": row[0],
            "based_on_sleep": row[2]
        }
    except Exception as e:
        return {"error": str(e)}