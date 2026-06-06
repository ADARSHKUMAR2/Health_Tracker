from pydantic import BaseModel
from agents import Runner
from openai_agents.health_agent import lead_health_coach 
from fastapi import FastAPI, HTTPException, APIRouter
from contextlib import asynccontextmanager
from backend.storage_s3 import download_db_from_s3, upload_db_to_s3
from openai_agents.schemas import ChatRequest, DailyHealthMetrics, SQL_Instructions
import sqlite3
from pathlib import Path
import logging
import json
from datetime import datetime

# Configure the logging format
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

WEBHOOK_URL = "http://192.168.1.12:8000/ingest-health"

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
        today_date = datetime.now().strftime("%Y-%m-%d")
        time_aware_prompt = f"(System Context: Today is {today_date}).\n\nUser Query: {request.message}"

        # The Runner handles tool execution and LLM reasoning asynchronously
        result = await Runner.run(lead_health_coach, time_aware_prompt)
        parsed_response = result.final_output.model_dump()

            # 🕵️‍♂️ AGENT EXECUTION TRACE
        logger.info("--- AGENT EXECUTION TRACE ---")
        try:
            # Safely look for 'history' or 'messages' without throwing an error
            trace_history = getattr(result, "history", getattr(result, "messages", []))
            
            for msg in trace_history:
                # Handle both dictionary formats and object formats
                role = msg.get("role", "unknown").upper() if isinstance(msg, dict) else getattr(msg, "role", "UNKNOWN").upper()
                content = msg.get("content") if isinstance(msg, dict) else getattr(msg, "content", None)
                tool_calls = msg.get("tool_calls") if isinstance(msg, dict) else getattr(msg, "tool_calls", None)

                if tool_calls:
                    logger.info(f"🔧 [{role} ACTION]: Triggered tool(s).")
                elif content:
                    logger.info(f"💬 [{role} MESSAGE]: {str(content)[:100]}...")
        except Exception as trace_err:
            logger.debug(f"Trace skipped: {trace_err}")
            
        logger.info("-----------------------------")

        return {
            "status": "success", 
            "response": parsed_response
        }
    except Exception as e:
        logger.error(f"❌ [CRITICAL ERROR in health_chat]: {str(e)}")
        return {"status": "error", "message": str(e)}

@router.post("/api/ingest-health")
async def ingest_health_data(metrics: DailyHealthMetrics):
    try:
        db_path = Path(__file__).resolve().parent.parent / "data" / "health_data.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Insert or update the row for today's date
        cursor.execute(
            SQL_Instructions, 
            (metrics.date, metrics.step_count, metrics.resting_hr, metrics.sleep_hours)
            )

        conn.commit()
        conn.close()

        # 🔗 Sync the fresh data to S3 immediately
        upload_db_to_s3()
        
        return {"status": "success", "message": f"Metrics for {metrics.date} saved & synced to S3!"}
    except Exception as e:
        logger.error(f"❌ [CRITICAL ERROR in ingest_health]: {str(e)}")
        return {"status": "error", "message": str(e)}

app.include_router(router)