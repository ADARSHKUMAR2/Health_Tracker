from pydantic import BaseModel
from agents import Runner
from openai_agents.health_agent import health_analyst_agent 
from fastapi import FastAPI, HTTPException, APIRouter
from contextlib import asynccontextmanager
from backend.storage_s3 import download_db_from_s3, upload_db_to_s3
from openai_agents.schemas import ChatRequest

# 1. Manage state on startup
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🎬 Server starting up...")
    download_db_from_s3()
    yield
    print("🛑 Server shutting down...")

router = APIRouter()

app = FastAPI(
    title="HealthAgent Backend",
    description="Main API for the HealthAgent",
    version="1.0.0",
    lifespan=lifespan
)

@router.post("/api/health-chat")
async def health_chat_endpoint(request: ChatRequest):
    """Passes the user's query to the OpenAI Health Agent."""
    try:
        # The Runner handles tool execution and LLM reasoning asynchronously
        result = await Runner.run(health_analyst_agent, request.message)
        
        return {
            "status": "success", 
            "response": result.final_output.model_dump()
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

app.include_router(router)