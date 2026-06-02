from agents import Agent, Runner
from shared.config import Config
from openai_agents.agent_tools.health_metrics_tool import fetch_health_metrics
import asyncio

# Create the Agent and give it the tool
health_analyst_agent = Agent(
    name="Health Analyst",
    instructions=(
        "You are a data-driven health coach. Analyze the user's biometric "
        "data to answer their questions clearly and provide actionable insights."
    ),
    tools=[fetch_health_metrics],
    model=Config.MODEL 
)

# Execute the run asynchronously
async def main():
    print("Agent is querying your database and thinking...")
    
    # The Runner handles the entire Loop (Thought -> Action -> Observation) automatically
    result = await Runner.run(
        health_analyst_agent, 
        "My runs have felt terrible the last 3 days. Look at my health data from 2026-05-29 to 2026-06-01 and tell me why I might be fatigued."
    )
    
    print("\n🩺 Final Analysis:")
    print(result.final_output)

if __name__ == "__main__":
    asyncio.run(main())