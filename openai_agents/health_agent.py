from agents import Agent, Runner, ModelSettings, function_tool
from openai.types.shared import responses_model
from shared.config import Config
from openai_agents.agent_tools.health_metrics_tool import fetch_health_metrics
from openai_agents.agent_tools.predict_tool import predict_tomorrow_metrics
import asyncio
from openai_agents.schemas import HealthAnalysisResponse, History_Instructions, Future_Instructions, Lead_Coach_Instructions

# Create the Agent and give it the tool
historical_analyst = Agent(
    name="Historical Analyst",
    handoff_description="Specialist agent for historical questions, past data, and previous trends.",
    instructions=History_Instructions,
    tools=[fetch_health_metrics],
    output_type=HealthAnalysisResponse
)

predictive_forecaster = Agent(
    name="Predictive Forecaster",
    handoff_description="Specialist agent for the future, predictions, or tomorrow's recovery.",
    instructions=Future_Instructions,
    tools=[predict_tomorrow_metrics],
    output_type=HealthAnalysisResponse
)

# --- 3. The Handoff Tools (Delegation) ---
@function_tool
async def consult_historical_analyst(query: str) -> str:
    """Call this tool to dispatch the Historical Analyst to check past metrics."""
    result = await Runner.run(historical_analyst, query)
    return str(result.final_output)

@function_tool
async def consult_predictive_forecaster(query: str) -> str:
    """Call this tool to dispatch the Predictive Forecaster to check tomorrow's metrics."""
    result = await Runner.run(predictive_forecaster, query)
    return str(result.final_output)

# --- 4. The Lead Coordinator Agent ---

lead_health_coach = Agent(
    name="Lead Health Coach",
    instructions=Lead_Coach_Instructions,
    tools=[consult_historical_analyst, consult_predictive_forecaster],
    output_type=HealthAnalysisResponse
)

# Execute the run asynchronously
# async def main():
#     print("Agent is querying your database and thinking...")
    
#     # The Runner handles the entire Loop (Thought -> Action -> Observation) automatically
#     result = await Runner.run(
#         health_analyst_agent, 
#         "Look at my health data from 2026-05-01 to 2026-05-30. What was my average step count, and did my resting heart rate trend up or down as the month progressed?"
#     )
    
#     print("\n🩺 Final Analysis:")
#     print(result.final_output)

# if __name__ == "__main__":
#     asyncio.run(main())