import os
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env file

def get_llm(temperature: float = 0.2):
    """
    Returns an instance of ChatOpenAI configured for either OpenRouter (local development)
    or a server-deployed OpenAI model (production/server environment), based on environment variables.
    """
    # Determine the environment
    environment = os.getenv("ENVIRONMENT", "local").lower()

    if environment == "local":

        return ChatOpenAI(
            model="google/gemini-2.0-flash-001",
            api_key=os.getenv("OPENROUTER_API_KEY", "your-openrouter-key"),
            base_url="https://openrouter.ai/api/v1",
            temperature=temperature,
            timeout=300,
            default_headers={
                "HTTP-Referer": os.getenv("OPENROUTER_REFERER", "http://localhost:8000"),
                "X-Title": os.getenv("OPENROUTER_TITLE", "RankPilot"),
            }
        )
    else:

        kwargs = {
            "model": "gpt-5.4-mini",
            "api_key": os.getenv("OPENAI_API_KEY", "your-openai-key"),
            "temperature": temperature
        }

        return ChatOpenAI(**kwargs)
