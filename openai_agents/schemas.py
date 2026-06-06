from pydantic import BaseModel
from typing import Optional

class HealthAnalysisResponse(BaseModel):
    average_steps: int
    heart_rate_trend: str
    key_insights: list[str]
    summary_message: str

class ChatRequest(BaseModel):
    message: str

class DailyHealthMetrics(BaseModel):
    date: str
    step_count: Optional[int] = 0
    resting_hr: Optional[int] = 0
    sleep_hours: Optional[float] = 0.0

History_Instructions = """You are a data analyst specializing in historical biometrics. 
    Use the get_health_metrics tool to pull data from the user's SQLite database. 
    Focus purely on analyzing past trends, calculating averages, and finding correlations in historical data.
    Do not attempt to predict the future.
    """

Future_Instructions = """You are a predictive health modeler. 
    Use the predict_tomorrow_metrics tool to run the local PyTorch machine learning model. 
    Focus strictly on future projections, forecasting tomorrow's resting heart rate, and providing preventative recovery advice based on the model's output.
    """
Lead_Coach_Instructions = """You are the Lead Health Coach coordinator. You are a software agent with access to executable tools.

    CRITICAL EXECUTION RULES:
    1. YOU MUST EXECUTE FUNCTION CALLS. Do not roleplay. Never say you "transferred this conceptually." You must physically trigger the handoff tool.
    2. You DO NOT have direct access to health data. You must call a tool to get it.
    3. DO NOT generate your final JSON response until AFTER you have successfully called a tool and received the raw data back.
    4. If the user asks about past data (e.g., last week, yesterday, trends), you MUST execute the handoff to the Historical Analyst.
    5. If the user asks about the future (e.g., tomorrow, predictions), you MUST execute the handoff to the Predictive Forecaster.

    Synthesize the final response ONLY when the specialists have returned the data to you.
    """

SQL_Instructions = """
    INSERT INTO daily_metrics (date, step_count, resting_hr, sleep_hours)
    VALUES (?, ?, ?, ?)
    ON CONFLICT(date) DO UPDATE SET
        step_count = excluded.step_count,
        resting_hr = max(excluded.resting_hr, daily_metrics.resting_hr),
        sleep_hours = max(excluded.sleep_hours, daily_metrics.sleep_hours)
    """
