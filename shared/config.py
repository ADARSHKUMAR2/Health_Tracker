import os
from dotenv import load_dotenv
load_dotenv()

from agents import OpenAIChatCompletionsModel
from openai import AsyncOpenAI

class Config:
    MODEL = "gpt-4o-mini"

    github_token = os.getenv("GITHUB_TOKEN")
    openai_key = os.getenv("OPENAI_API_KEY")

    github_client = AsyncOpenAI(
        base_url="https://models.inference.ai.azure.com",
        api_key=github_token
    )

    github_model = OpenAIChatCompletionsModel(
        model=MODEL,
        openai_client=github_client
    )