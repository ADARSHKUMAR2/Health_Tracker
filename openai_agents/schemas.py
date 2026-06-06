from pydantic import BaseModel

class HealthAnalysisResponse(BaseModel):
    average_steps: int
    heart_rate_trend: str
    key_insights: list[str]
    summary_message: str

class ChatRequest(BaseModel):
    message: str

