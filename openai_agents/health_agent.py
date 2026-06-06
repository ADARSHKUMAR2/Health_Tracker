from agents import Agent, Runner, ModelSettings
from shared.config import Config
from openai_agents.agent_tools.health_metrics_tool import fetch_health_metrics
import asyncio
from openai_agents.schemas import HealthAnalysisResponse 

# Create the Agent and give it the tool
health_analyst_agent = Agent(
    name="Health Analyst",
    instructions=(
        "You are a data-driven health coach. Analyze the user's biometric "
        "data to answer their questions clearly and provide actionable insights."
    ),
    tools=[fetch_health_metrics],
    model=Config.MODEL ,
    output_type=HealthAnalysisResponse,
    model_settings=ModelSettings(tool_choice="required")
)

# Execute the run asynchronously
async def main():
    print("Agent is querying your database and thinking...")
    
    # The Runner handles the entire Loop (Thought -> Action -> Observation) automatically
    result = await Runner.run(
        health_analyst_agent, 
        "Look at my health data from 2026-05-01 to 2026-05-30. What was my average step count, and did my resting heart rate trend up or down as the month progressed?"
    )
    
    print("\n🩺 Final Analysis:")
    print(result.final_output)

if __name__ == "__main__":
    asyncio.run(main())