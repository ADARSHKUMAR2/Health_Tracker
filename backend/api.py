from pydantic import BaseModel
from agents import Runner
from openai_agents.health_agent import health_analyst_agent 
from fastapi import FastAPI, HTTPException, APIRouter

class ChatRequest(BaseModel):
    message: str

router = APIRouter()

app = FastAPI(
    title="HealthAgent Backend",
    description="Main API for the HealthAgent",
    version="1.0.0"
)

@router.post("/api/health-chat")
async def health_chat_endpoint(request: ChatRequest):
    """Passes the user's query to the OpenAI Health Agent."""
    try:
        # The Runner handles tool execution and LLM reasoning asynchronously
        result = await Runner.run(health_analyst_agent, request.message)
        
        return {
            "status": "success", 
            "response": result.final_output
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}