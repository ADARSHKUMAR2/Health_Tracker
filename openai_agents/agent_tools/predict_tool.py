# agent/tools/predict_tool.py
import json

from agents import function_tool
from ML.predict import get_tomorrows_hr_prediction

@function_tool
def predict_tomorrow_metrics() -> str:
    """
    Use this tool to predict the user's resting heart rate for tomorrow 
    based on a local PyTorch machine learning model.
    """
    prediction_data = get_tomorrows_hr_prediction()
    return json.dumps(prediction_data)